#!/usr/bin/env python3
"""
CivicMind AI — Inference Latency & Throughput Benchmark
Measures p50, p95, p99 latency and requests/sec on GPU/CPU for MuRIL v1.1.
Saves results to artifacts/evaluation/inference_benchmark.json.
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import numpy as np

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Windows UTF-8 console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import torch
from transformers import AutoTokenizer
from app.ml.model import MuRILMultiTaskForCivic
from app.ml.extraction.lightweight_extractor import LightweightCivicExtractor

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

BENCHMARK_PROMPTS = [
    "Street light not working in Anna Nagar 2nd avenue for 4 days.",
    "Road pothole near bus stand is very dangerous causing accidents.",
    "Water supply cut for past 3 days in Gandhi street, 50 families suffering.",
    "thanni varala 3 days ah",
    "bijli chali gayi hai kal raat se mohalla mein",
    "Open manhole with sparking transformer opposite to government hospital.",
    "Garbage not collected for 2 weeks in Ward 14.",
    "Hello sir how are you",
    "How do I apply for a new water connection?",
    "Drainage overflow mixed with drinking water in market road.",
]


def benchmark_model(
    model_dir: str = "models/grievance/v1.1",
    output_path: str = "artifacts/evaluation/inference_benchmark.json",
    num_warmup: int = 10,
    num_runs: int = 100,
):
    m_path = Path(model_dir)
    if not m_path.exists():
        logger.error(f"Model directory {model_dir} does not exist.")
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    logger.info(f"Running inference benchmark on {device_name} ({device})...")

    model = MuRILMultiTaskForCivic.from_pretrained(m_path)
    model.to(device)
    model.eval()

    tokenizer_path = m_path / "encoder" if (m_path / "encoder").exists() else "models/muril-base-cased"
    tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_path))

    # 1. Warmup
    logger.info(f"Warming up ({num_warmup} iterations)...")
    for _ in range(num_warmup):
        text = BENCHMARK_PROMPTS[0]
        enc = tokenizer([text], max_length=128, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            _ = model.predict(enc["input_ids"].to(device), enc["attention_mask"].to(device))

    # 2. Single Query Latency (End-to-End: Tokenization + Model + Extractor)
    logger.info(f"Measuring Single-Item End-to-End Latency ({num_runs} iterations)...")
    latencies_e2e_ms = []
    latencies_model_ms = []
    latencies_extract_ms = []

    for i in range(num_runs):
        text = BENCHMARK_PROMPTS[i % len(BENCHMARK_PROMPTS)]
        
        t0 = time.perf_counter()
        # Rule extraction
        t_ext_0 = time.perf_counter()
        entities = LightweightCivicExtractor.extract_entities(text)
        t_ext_1 = time.perf_counter()
        
        # Tokenization + Model
        t_mod_0 = time.perf_counter()
        enc = tokenizer([text], max_length=128, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            preds = model.predict(enc["input_ids"].to(device), enc["attention_mask"].to(device))
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        t_mod_1 = time.perf_counter()
        
        # Escalation rule
        is_esc, reasons, sla = LightweightCivicExtractor.determine_escalation_rules(
            text, entities, preds[0]["priority"], preds[0]["severity"], preds[0]["category"]
        )
        t1 = time.perf_counter()

        latencies_e2e_ms.append((t1 - t0) * 1000)
        latencies_model_ms.append((t_mod_1 - t_mod_0) * 1000)
        latencies_extract_ms.append((t_ext_1 - t_ext_0) * 1000)

    # 3. Batch Throughput Tests (Batch sizes: 1, 8, 16, 32, 64)
    batch_sizes = [1, 8, 16, 32, 64]
    throughput_results = {}

    for bs in batch_sizes:
        batch_texts = [BENCHMARK_PROMPTS[j % len(BENCHMARK_PROMPTS)] for j in range(bs)]
        enc = tokenizer(batch_texts, max_length=128, padding=True, truncation=True, return_tensors="pt")
        input_ids = enc["input_ids"].to(device)
        attention_mask = enc["attention_mask"].to(device)

        batch_times = []
        for _ in range(20):
            t_b0 = time.perf_counter()
            with torch.no_grad():
                _ = model.predict(input_ids, attention_mask)
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            t_b1 = time.perf_counter()
            batch_times.append(t_b1 - t_b0)

        avg_time = float(np.mean(batch_times))
        items_per_sec = bs / avg_time
        throughput_results[f"batch_{bs}"] = {
            "batch_size": bs,
            "avg_latency_ms": round(avg_time * 1000, 2),
            "throughput_items_per_sec": round(items_per_sec, 2),
        }

    benchmark_data = {
        "model_version": "v1.1",
        "device": device_name,
        "single_query_e2e": {
            "p50_ms": round(float(np.percentile(latencies_e2e_ms, 50)), 2),
            "p95_ms": round(float(np.percentile(latencies_e2e_ms, 95)), 2),
            "p99_ms": round(float(np.percentile(latencies_e2e_ms, 99)), 2),
            "mean_ms": round(float(np.mean(latencies_e2e_ms)), 2),
        },
        "model_only": {
            "p50_ms": round(float(np.percentile(latencies_model_ms, 50)), 2),
            "p95_ms": round(float(np.percentile(latencies_model_ms, 95)), 2),
            "mean_ms": round(float(np.mean(latencies_model_ms)), 2),
        },
        "extractor_latency": {
            "p50_ms": round(float(np.percentile(latencies_extract_ms, 50)), 4),
            "mean_ms": round(float(np.mean(latencies_extract_ms)), 4),
        },
        "batch_throughput": throughput_results,
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2)

    logger.info(f"✅ Benchmark completed! Single Query Latency: p50={benchmark_data['single_query_e2e']['p50_ms']}ms, p95={benchmark_data['single_query_e2e']['p95_ms']}ms")
    logger.info(f"Batch 32 Throughput: {throughput_results['batch_32']['throughput_items_per_sec']} items/sec")
    logger.info(f"Saved benchmark report to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=str, default="models/grievance/v1.1")
    parser.add_argument("--output-path", type=str, default="artifacts/evaluation/inference_benchmark.json")
    args = parser.parse_args()
    benchmark_model(model_dir=args.model_dir, output_path=args.output_path)
