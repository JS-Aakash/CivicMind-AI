"""
CivicMind AI — Module 3 Latency Benchmark
Measures latency breakdown across the 5 stages of the Module 3 pipeline:
1. Classification Latency (IndicLID + MuRIL v1.1)
2. Extraction Latency (Lightweight Regex & Entity Extractor)
3. Priority Engine Latency (Rules + Safety Override + Hybrid Scoring)
4. Routing Engine Latency (Single & Multi-Issue Department Mapping)
5. SLA Engine Latency (Turnaround Window & Status Computation)
6. Total End-to-End Decision Latency

Outputs: backend/artifacts/evaluation/module3_latency.json
"""

import sys
import os
import io
import time
import json
import statistics
import numpy as np

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.muril_classifier import muril_classifier_service
from app.services.language_service import language_detection_service
from app.services.interfaces import LanguageInfo
from app.ml.extraction.lightweight_extractor import LightweightCivicExtractor
from app.priority.priority_engine import evaluate_priority
from app.routing.routing_engine import route_complaint
from app.routing.sla_engine import calculate_sla
from app.routing.review_policy import evaluate_review_decision
from app.priority.priority_explanation import generate_priority_explanation


def benchmark_module3(num_iterations: int = 50):
    print("=" * 70)
    print("  CIVICMIND AI — MODULE 3 DECISION LATENCY BENCHMARK")
    print("=" * 70)
    print(f"Running {num_iterations} benchmark iterations on MuRIL v1.1 + Module 3 Pipeline...")

    test_sentences = [
        "Anna 3 days ah water varala, whole street affected.",
        "There is a severe pothole on the main road near school.",
        "Road la live electric wire fallen, children are passing nearby.",
        "Waterlogged street and drainage overflow after heavy rainfall.",
        "Street light not working in residential colony for 1 week.",
        "Garbage pile accumulating outside government hospital entrance.",
        "Bus route 45B not arriving on schedule since yesterday morning.",
        "What is the contact number for electricity department emergency?",
    ]

    classification_latencies = []
    extraction_latencies = []
    priority_latencies = []
    routing_latencies = []
    sla_latencies = []
    total_latencies = []

    dummy_lang = LanguageInfo(
        primary_language="en",
        language_name="English",
        languages=["en"],
        script="roman",
        is_code_mixed=False,
        confidence=0.95,
    )

    # Warmup
    for text in test_sentences[:2]:
        _ = muril_classifier_service.predict_detailed(text, dummy_lang)

    for i in range(num_iterations):
        text = test_sentences[i % len(test_sentences)]
        t_total_start = time.perf_counter()

        # 1. Classification
        t0 = time.perf_counter()
        pred = muril_classifier_service.predict_detailed(text, dummy_lang)
        t1 = time.perf_counter()
        classification_latencies.append((t1 - t0) * 1000)

        # 2. Entity Extraction
        t2 = time.perf_counter()
        entities = LightweightCivicExtractor.extract_entities(text)
        t3 = time.perf_counter()
        extraction_latencies.append((t3 - t2) * 1000)


        # 3. Priority Engine
        t4 = time.perf_counter()
        p_res = evaluate_priority(
            neural_pred=pred["priority"],
            neural_prob=pred["priority_confidence"],
            neural_probs=pred.get("task_confidences", {"priority": pred["priority_confidence"]}),
            severity=pred["severity"],
            text=text,
            category=pred["category"],
            subcategory=pred.get("subcategory"),
            entities=entities.to_dict() if hasattr(entities, "to_dict") else {},
        )
        t5 = time.perf_counter()
        priority_latencies.append((t5 - t4) * 1000)

        # 4. Routing Engine
        t6 = time.perf_counter()
        r_res = route_complaint(
            primary_category=pred["category"],
            primary_subcategory=pred.get("subcategory"),
            category_confidence=pred["category_confidence"],
            multi_issues=pred.get("secondary_categories", []),
        )
        rev_res = evaluate_review_decision(
            routing_confidence=r_res.primary_department.confidence,
            priority=p_res.final_priority,
            is_safety_hazard=p_res.context_signals.get("safety_risk", False),
        )
        t7 = time.perf_counter()
        routing_latencies.append((t7 - t6) * 1000)

        # 5. SLA Engine & Explanation
        t8 = time.perf_counter()
        sla_res = calculate_sla(
            priority=p_res.final_priority,
            department_id=r_res.primary_department.id,
        )
        exp_res = generate_priority_explanation(
            category=pred["category"],
            subcategory=pred.get("subcategory"),
            final_priority=p_res.final_priority,
            neural_priority=pred["priority"],
            context_signals=p_res.context_signals,
            department_name=r_res.primary_department.name,
            sla_window_hours=sla_res.response_window_hours,
            is_safety_override=p_res.reasoning_mode == "safety_override",
            requires_human_review=rev_res.requires_human_review,
        )
        t9 = time.perf_counter()
        sla_latencies.append((t9 - t8) * 1000)

        t_total_end = time.perf_counter()
        total_latencies.append((t_total_end - t_total_start) * 1000)

    def calc_stats(arr):
        return {
            "mean_ms": round(float(np.mean(arr)), 3),
            "p50_ms": round(float(np.median(arr)), 3),
            "p95_ms": round(float(np.percentile(arr, 95)), 3),
            "p99_ms": round(float(np.percentile(arr, 99)), 3),
            "min_ms": round(float(np.min(arr)), 3),
            "max_ms": round(float(np.max(arr)), 3),
        }

    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_version": "muril-v1.1",
        "device": str(muril_classifier_service.device),
        "iterations": num_iterations,
        "breakdown": {
            "classification": calc_stats(classification_latencies),
            "entity_extraction": calc_stats(extraction_latencies),
            "priority_engine": calc_stats(priority_latencies),
            "routing_engine": calc_stats(routing_latencies),
            "sla_and_explanation": calc_stats(sla_latencies),
        },
        "total_decision_latency": calc_stats(total_latencies),
    }

    print("\n--- LATENCY BREAKDOWN (ms) ---")
    print(f"1. Neural Classification : Mean = {results['breakdown']['classification']['mean_ms']} ms | p50 = {results['breakdown']['classification']['p50_ms']} ms | p95 = {results['breakdown']['classification']['p95_ms']} ms")
    print(f"2. Entity Extraction     : Mean = {results['breakdown']['entity_extraction']['mean_ms']} ms | p50 = {results['breakdown']['entity_extraction']['p50_ms']} ms | p95 = {results['breakdown']['entity_extraction']['p95_ms']} ms")
    print(f"3. Priority Engine       : Mean = {results['breakdown']['priority_engine']['mean_ms']} ms | p50 = {results['breakdown']['priority_engine']['p50_ms']} ms | p95 = {results['breakdown']['priority_engine']['p95_ms']} ms")
    print(f"4. Routing & Review      : Mean = {results['breakdown']['routing_engine']['mean_ms']} ms | p50 = {results['breakdown']['routing_engine']['p50_ms']} ms | p95 = {results['breakdown']['routing_engine']['p95_ms']} ms")
    print(f"5. SLA & Explanation     : Mean = {results['breakdown']['sla_and_explanation']['mean_ms']} ms | p50 = {results['breakdown']['sla_and_explanation']['p50_ms']} ms | p95 = {results['breakdown']['sla_and_explanation']['p95_ms']} ms")
    print("-" * 70)
    print(f"TOTAL DECISION LATENCY   : Mean = {results['total_decision_latency']['mean_ms']} ms | p50 = {results['total_decision_latency']['p50_ms']} ms | p95 = {results['total_decision_latency']['p95_ms']} ms")
    print("=" * 70)

    # Save to artifacts directory
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "artifacts", "evaluation"))
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "module3_latency.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Saved benchmark results to {out_file}")
    return results


if __name__ == "__main__":
    benchmark_module3(num_iterations=50)
