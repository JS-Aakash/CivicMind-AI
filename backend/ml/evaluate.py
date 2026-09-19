#!/usr/bin/env python3
"""
CivicMind AI — Comprehensive Model Evaluation Suite (v1.0 vs v1.1 Comparative Analysis)
Evaluates MuRIL v1.0 and MuRIL v1.1 on:
1. Standard Test Set (1,494 samples — 100% UNTOUCHED)
2. Challenge Set (750 adversarial samples — 100% UNTOUCHED)

Generates:
- artifacts/evaluation/v1_vs_v1_1.json
- artifacts/evaluation/v1_vs_v1_1.md
- artifacts/evaluation/error_analysis_v1_1.json
- artifacts/evaluation/challenge_slices_v1_1.json
"""
import argparse
import json
import logging
import math
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Windows UTF-8 console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import numpy as np
import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from transformers import AutoTokenizer

from app.core.config import settings
from app.ml.calibration.temperature_scaling import compute_ece, compute_brier_score
from app.ml.model import MuRILMultiTaskForCivic
from app.ml.taxonomy import (
    CATEGORIES,
    ALL_SUBCATEGORIES,
    PRIORITIES,
    SEVERITIES,
    CATEGORY_TO_IDX,
    IDX_TO_CATEGORY,
    SUBCATEGORY_TO_IDX,
    IDX_TO_SUBCATEGORY,
    PRIORITY_TO_IDX,
    IDX_TO_PRIORITY,
    SEVERITY_TO_IDX,
    IDX_TO_SEVERITY,
    GRIEVANCE_TO_IDX,
    IDX_TO_GRIEVANCE,
    get_scoped_subcategory,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def compute_task_metrics(y_true: List[int], y_pred: List[int], label_names: List[str]) -> Dict[str, Any]:
    acc = accuracy_score(y_true, y_pred)
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted", zero_division=0)

    # Per-class metrics
    p_class, r_class, f1_class, support = precision_recall_fscore_support(y_true, y_pred, labels=list(range(len(label_names))), zero_division=0)
    per_class = {
        label_names[idx]: {
            "precision": round(float(p_class[idx]), 4),
            "recall": round(float(r_class[idx]), 4),
            "f1": round(float(f1_class[idx]), 4),
            "support": int(support[idx]),
        }
        for idx in range(len(label_names))
    }

    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(label_names)))).tolist()

    return {
        "accuracy": round(float(acc), 4),
        "macro_precision": round(float(p_macro), 4),
        "macro_recall": round(float(r_macro), 4),
        "macro_f1": round(float(f1_macro), 4),
        "weighted_precision": round(float(p_weighted), 4),
        "weighted_recall": round(float(r_weighted), 4),
        "weighted_f1": round(float(f1_weighted), 4),
        "per_class": per_class,
        "labels": label_names,
        "confusion_matrix": cm,
    }


def evaluate_single_checkpoint(
    model: MuRILMultiTaskForCivic,
    tokenizer,
    dataset: List[Dict[str, Any]],
    device: torch.device,
    batch_size: int = 32,
) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]], np.ndarray]:
    """Evaluates a single model checkpoint on the provided dataset."""
    y_true_g, y_pred_g = [], []
    y_true_c, y_pred_c = [], []
    y_true_sub, y_pred_sub = [], []
    y_true_s, y_pred_s = [], []
    y_true_p, y_pred_p = [], []

    all_cat_probs = []
    lang_buckets = defaultdict(lambda: {"true_c": [], "pred_c": [], "true_g": [], "pred_g": [], "true_p": [], "pred_p": []})
    error_cases = []

    for i in range(0, len(dataset), batch_size):
        batch = dataset[i : i + batch_size]
        texts = [b.get("text", "") for b in batch]

        enc = tokenizer(texts, padding=True, truncation=True, max_length=128, return_tensors="pt")
        input_ids = enc["input_ids"].to(device)
        attention_mask = enc["attention_mask"].to(device)

        preds = model.predict(input_ids, attention_mask)

        for b, p in zip(batch, preds):
            t_g = GRIEVANCE_TO_IDX.get(b.get("is_grievance", True), 1)
            t_c = CATEGORY_TO_IDX.get(b.get("category", "other"), CATEGORY_TO_IDX["other"])
            scoped_true_sub = get_scoped_subcategory(b.get("category", "other"), b.get("subcategory", "other"))
            t_sub = SUBCATEGORY_TO_IDX.get(scoped_true_sub, 0)
            t_s = SEVERITY_TO_IDX.get(b.get("severity", "medium"), SEVERITY_TO_IDX["medium"])
            t_p = PRIORITY_TO_IDX.get(b.get("priority", "medium"), PRIORITY_TO_IDX["medium"])

            p_g = GRIEVANCE_TO_IDX.get(p["is_grievance"], 1)
            p_c = CATEGORY_TO_IDX.get(p["category"], CATEGORY_TO_IDX["other"])
            scoped_pred_sub = get_scoped_subcategory(p["category"], p["subcategory"])
            p_sub = SUBCATEGORY_TO_IDX.get(scoped_pred_sub, 0)
            p_s = SEVERITY_TO_IDX.get(p["severity"], SEVERITY_TO_IDX["medium"])
            p_p = PRIORITY_TO_IDX.get(p["priority"], PRIORITY_TO_IDX["medium"])

            y_true_g.append(t_g)
            y_pred_g.append(p_g)
            y_true_c.append(t_c)
            y_pred_c.append(p_c)
            y_true_sub.append(t_sub)
            y_pred_sub.append(p_sub)
            y_true_s.append(t_s)
            y_pred_s.append(p_s)
            y_true_p.append(t_p)
            y_pred_p.append(p_p)

            # Language bucket
            lang = b.get("language", "en")
            lang_buckets[lang]["true_c"].append(t_c)
            lang_buckets[lang]["pred_c"].append(p_c)
            lang_buckets[lang]["true_g"].append(t_g)
            lang_buckets[lang]["pred_g"].append(p_g)
            lang_buckets[lang]["true_p"].append(t_p)
            lang_buckets[lang]["pred_p"].append(p_p)

            # Construct category probability vector for ECE
            prob_vec = [p["category_probabilities"].get(cat, 0.0) for cat in CATEGORIES]
            all_cat_probs.append(prob_vec)

            # Record error if category, grievance, or priority was wrong
            if p_c != t_c or p_g != t_g or p_p != t_p:
                error_cases.append({
                    "text": b.get("text", ""),
                    "language": lang,
                    "challenge_group": b.get("challenge_group", "standard"),
                    "true_grievance": b.get("is_grievance", True),
                    "pred_grievance": p["is_grievance"],
                    "true_category": b.get("category", "other"),
                    "pred_category": p["category"],
                    "category_conf": p["category_confidence"],
                    "true_priority": b.get("priority", "medium"),
                    "pred_priority": p["priority"],
                    "priority_conf": p["priority_confidence"],
                })

    # Metrics per task
    task_metrics = {
        "grievance": compute_task_metrics(y_true_g, y_pred_g, ["non_grievance", "genuine_grievance"]),
        "category": compute_task_metrics(y_true_c, y_pred_c, CATEGORIES),
        "subcategory": compute_task_metrics(y_true_sub, y_pred_sub, ALL_SUBCATEGORIES),
        "severity": compute_task_metrics(y_true_s, y_pred_s, SEVERITIES),
        "priority": compute_task_metrics(y_true_p, y_pred_p, PRIORITIES),
    }

    # Language breakdown
    lang_metrics = {}
    for lang, ldata in lang_buckets.items():
        if len(ldata["true_c"]) > 0:
            cat_acc = accuracy_score(ldata["true_c"], ldata["pred_c"])
            cat_f1 = precision_recall_fscore_support(ldata["true_c"], ldata["pred_c"], average="macro", zero_division=0)[2]
            prio_acc = accuracy_score(ldata["true_p"], ldata["pred_p"])
            griev_acc = accuracy_score(ldata["true_g"], ldata["pred_g"])
            lang_metrics[lang] = {
                "sample_count": len(ldata["true_c"]),
                "category_accuracy": round(float(cat_acc), 4),
                "category_macro_f1": round(float(cat_f1), 4),
                "priority_accuracy": round(float(prio_acc), 4),
                "grievance_accuracy": round(float(griev_acc), 4),
            }

    cat_probs_np = np.array(all_cat_probs)
    # Normalize probabilities row-wise if not perfectly 1.0
    row_sums = cat_probs_np.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    cat_probs_np = cat_probs_np / row_sums

    # Calibration on test set
    ece = compute_ece(cat_probs_np, np.array(y_true_c))
    brier = compute_brier_score(cat_probs_np, np.array(y_true_c), len(CATEGORIES))
    task_metrics["calibration"] = {
        "category_ece": round(ece, 4),
        "category_brier": round(brier, 4),
    }

    return task_metrics, lang_metrics, error_cases, cat_probs_np


def evaluate_challenge_slices(
    model: MuRILMultiTaskForCivic,
    tokenizer,
    challenge_data: List[Dict[str, Any]],
    device: torch.device,
) -> Dict[str, Any]:
    """Evaluates granular slices of challenge dataset."""
    groups = defaultdict(list)
    for item in challenge_data:
        grp = item.get("challenge_group", "unknown")
        groups[grp].append(item)

    slice_results = {}
    for grp, items in groups.items():
        texts = [it["text"] for it in items]
        enc = tokenizer(texts, padding=True, truncation=True, max_length=128, return_tensors="pt")
        with torch.no_grad():
            preds = model.predict(enc["input_ids"].to(device), enc["attention_mask"].to(device))

        correct_c = 0
        correct_g = 0
        correct_p = 0
        for it, p in zip(items, preds):
            if p["category"] == it.get("category"):
                correct_c += 1
            if p["is_grievance"] == it.get("is_grievance"):
                correct_g += 1
            if p["priority"] == it.get("priority"):
                correct_p += 1

        n = len(items)
        slice_results[grp] = {
            "samples": n,
            "category_accuracy": round(correct_c / n, 4) if n > 0 else 0.0,
            "grievance_accuracy": round(correct_g / n, 4) if n > 0 else 0.0,
            "priority_accuracy": round(correct_p / n, 4) if n > 0 else 0.0,
        }

    return slice_results


def run_comparative_evaluation(
    model_v1_dir: str = "models/grievance/v1",
    model_v1_1_dir: str = "models/grievance/v1.1",
    test_path: str = "data/test.json",
    challenge_path: str = "data/challenge.json",
    artifacts_dir: str = "artifacts/evaluation",
):
    art_path = Path(artifacts_dir)
    art_path.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device {device} for comparative evaluation...")

    # Load datasets
    with open(test_path, "r", encoding="utf-8") as f:
        test_data = json.load(f)
    with open(challenge_path, "r", encoding="utf-8") as f:
        challenge_data = json.load(f)

    logger.info(f"Loaded Test Set: {len(test_data)} samples | Challenge Set: {len(challenge_data)} samples")

    # Load Models
    logger.info(f"Loading MuRIL v1.0 from {model_v1_dir}...")
    model_v1 = MuRILMultiTaskForCivic.from_pretrained(model_v1_dir)
    model_v1.to(device)
    model_v1.eval()

    logger.info(f"Loading MuRIL v1.1 from {model_v1_1_dir}...")
    model_v1_1 = MuRILMultiTaskForCivic.from_pretrained(model_v1_1_dir)
    model_v1_1.to(device)
    model_v1_1.eval()

    tok_dir = Path(model_v1_1_dir) / "encoder"
    tokenizer = AutoTokenizer.from_pretrained(str(tok_dir) if tok_dir.exists() else "models/muril-base-cased")

    # 1. Evaluate v1.0 on Test Set
    logger.info("Evaluating MuRIL v1.0 on Test Set...")
    v1_test_task, v1_test_lang, v1_errors, _ = evaluate_single_checkpoint(model_v1, tokenizer, test_data, device)

    # 2. Evaluate v1.1 on Test Set
    logger.info("Evaluating MuRIL v1.1 on Test Set...")
    v1_1_test_task, v1_1_test_lang, v1_1_errors, _ = evaluate_single_checkpoint(model_v1_1, tokenizer, test_data, device)

    # 3. Evaluate v1.0 & v1.1 on Challenge Set
    logger.info("Evaluating MuRIL v1.0 & v1.1 on Challenge Set...")
    v1_chal_task, v1_chal_lang, _, _ = evaluate_single_checkpoint(model_v1, tokenizer, challenge_data, device)
    v1_1_chal_task, v1_1_chal_lang, v1_1_chal_errors, _ = evaluate_single_checkpoint(model_v1_1, tokenizer, challenge_data, device)

    # 4. Evaluate Challenge Slices
    v1_slices = evaluate_challenge_slices(model_v1, tokenizer, challenge_data, device)
    v1_1_slices = evaluate_challenge_slices(model_v1_1, tokenizer, challenge_data, device)

    # Build Comparative Report JSON
    comparison_report = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
            "test_samples": len(test_data),
            "challenge_samples": len(challenge_data),
        },
        "test_set_comparison": {
            "grievance_detection": {
                "v1_0_macro_f1": v1_test_task["grievance"]["macro_f1"],
                "v1_1_macro_f1": v1_1_test_task["grievance"]["macro_f1"],
                "v1_0_accuracy": v1_test_task["grievance"]["accuracy"],
                "v1_1_accuracy": v1_1_test_task["grievance"]["accuracy"],
                "improvement_f1": round(v1_1_test_task["grievance"]["macro_f1"] - v1_test_task["grievance"]["macro_f1"], 4),
            },
            "category_classification": {
                "v1_0_macro_f1": v1_test_task["category"]["macro_f1"],
                "v1_1_macro_f1": v1_1_test_task["category"]["macro_f1"],
                "v1_0_accuracy": v1_test_task["category"]["accuracy"],
                "v1_1_accuracy": v1_1_test_task["category"]["accuracy"],
                "improvement_f1": round(v1_1_test_task["category"]["macro_f1"] - v1_test_task["category"]["macro_f1"], 4),
            },
            "priority_classification": {
                "v1_0_macro_f1": v1_test_task["priority"]["macro_f1"],
                "v1_1_macro_f1": v1_1_test_task["priority"]["macro_f1"],
                "v1_0_accuracy": v1_test_task["priority"]["accuracy"],
                "v1_1_accuracy": v1_1_test_task["priority"]["accuracy"],
                "improvement_f1": round(v1_1_test_task["priority"]["macro_f1"] - v1_test_task["priority"]["macro_f1"], 4),
            },
            "severity_classification": {
                "v1_0_macro_f1": v1_test_task["severity"]["macro_f1"],
                "v1_1_macro_f1": v1_1_test_task["severity"]["macro_f1"],
                "v1_0_accuracy": v1_test_task["severity"]["accuracy"],
                "v1_1_accuracy": v1_1_test_task["severity"]["accuracy"],
                "improvement_f1": round(v1_1_test_task["severity"]["macro_f1"] - v1_test_task["severity"]["macro_f1"], 4),
            },
            "subcategory_classification": {
                "v1_0_macro_f1": v1_test_task["subcategory"]["macro_f1"],
                "v1_1_macro_f1": v1_1_test_task["subcategory"]["macro_f1"],
                "v1_0_accuracy": v1_test_task["subcategory"]["accuracy"],
                "v1_1_accuracy": v1_1_test_task["subcategory"]["accuracy"],
                "improvement_f1": round(v1_1_test_task["subcategory"]["macro_f1"] - v1_test_task["subcategory"]["macro_f1"], 4),
            },
            "calibration_ece": {
                "v1_0_ece": v1_test_task["calibration"]["category_ece"],
                "v1_1_ece": v1_1_test_task["calibration"]["category_ece"],
                "ece_reduction": round(v1_test_task["calibration"]["category_ece"] - v1_1_test_task["calibration"]["category_ece"], 4),
            },
        },
        "language_breakdown_category_f1": {
            lang: {
                "samples": v1_test_lang[lang]["sample_count"],
                "v1_0_f1": v1_test_lang[lang]["category_macro_f1"],
                "v1_1_f1": v1_1_test_lang[lang]["category_macro_f1"],
                "improvement": round(v1_1_test_lang[lang]["category_macro_f1"] - v1_test_lang[lang]["category_macro_f1"], 4),
            }
            for lang in v1_test_lang
        },
        "challenge_set_overall": {
            "v1_0_category_acc": v1_chal_task["category"]["accuracy"],
            "v1_1_category_acc": v1_1_chal_task["category"]["accuracy"],
            "v1_0_grievance_acc": v1_chal_task["grievance"]["accuracy"],
            "v1_1_grievance_acc": v1_1_chal_task["grievance"]["accuracy"],
            "v1_0_priority_acc": v1_chal_task["priority"]["accuracy"],
            "v1_1_priority_acc": v1_1_chal_task["priority"]["accuracy"],
        },
        "challenge_slices_comparison": {
            grp: {
                "samples": v1_1_slices[grp]["samples"],
                "v1_0_category_acc": v1_slices.get(grp, {}).get("category_accuracy", 0.0),
                "v1_1_category_acc": v1_1_slices[grp]["category_accuracy"],
                "v1_0_grievance_acc": v1_slices.get(grp, {}).get("grievance_accuracy", 0.0),
                "v1_1_grievance_acc": v1_1_slices[grp]["grievance_accuracy"],
            }
            for grp in v1_1_slices
        },
        "v1_1_full_task_metrics": v1_1_test_task,
    }

    # Save JSON files
    with open(art_path / "v1_vs_v1_1.json", "w", encoding="utf-8") as f:
        json.dump(comparison_report, f, indent=2)

    with open(art_path / "challenge_slices_v1_1.json", "w", encoding="utf-8") as f:
        json.dump(v1_1_slices, f, indent=2)

    with open(art_path / "error_analysis_v1_1.json", "w", encoding="utf-8") as f:
        json.dump({
            "test_set_error_count": len(v1_1_errors),
            "challenge_set_error_count": len(v1_1_chal_errors),
            "sample_test_errors": v1_1_errors[:25],
            "sample_challenge_errors": v1_1_chal_errors[:25],
        }, f, indent=2)

    # Generate Markdown Report
    generate_markdown_report(comparison_report, art_path / "v1_vs_v1_1.md")
    logger.info(f"✅ Comparative Evaluation Complete! Artifacts written to {art_path}")


def generate_markdown_report(report: Dict[str, Any], output_path: Path):
    tc = report["test_set_comparison"]
    lb = report["language_breakdown_category_f1"]
    cs = report["challenge_slices_comparison"]
    co = report["challenge_set_overall"]

    md = f"""# CivicMind AI — MuRIL v1.0 vs MuRIL v1.1 Comparative Evaluation Report

**Generated**: {report['metadata']['timestamp']}
**Hardware Device**: {report['metadata']['device']}
**Test Set Size**: {report['metadata']['test_samples']} samples (100% UNTOUCHED)
**Challenge Set Size**: {report['metadata']['challenge_samples']} samples (100% UNTOUCHED)

---

## 1. Executive Summary & Core Task Metrics (Standard Test Set)

| Task Head | v1.0 Macro F1 | v1.1 Macro F1 | v1.0 Accuracy | v1.1 Accuracy | $\\Delta$ F1 Gain |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Grievance Detection** | {tc['grievance_detection']['v1_0_macro_f1']*100:.2f}% | **{tc['grievance_detection']['v1_1_macro_f1']*100:.2f}%** | {tc['grievance_detection']['v1_0_accuracy']*100:.2f}% | **{tc['grievance_detection']['v1_1_accuracy']*100:.2f}%** | +{tc['grievance_detection']['improvement_f1']*100:.2f}% |
| **Primary Category** | {tc['category_classification']['v1_0_macro_f1']*100:.2f}% | **{tc['category_classification']['v1_1_macro_f1']*100:.2f}%** | {tc['category_classification']['v1_0_accuracy']*100:.2f}% | **{tc['category_classification']['v1_1_accuracy']*100:.2f}%** | +{tc['category_classification']['improvement_f1']*100:.2f}% |
| **Subcategory (Hierarchical)** | {tc['subcategory_classification']['v1_0_macro_f1']*100:.2f}% | **{tc['subcategory_classification']['v1_1_macro_f1']*100:.2f}%** | {tc['subcategory_classification']['v1_0_accuracy']*100:.2f}% | **{tc['subcategory_classification']['v1_1_accuracy']*100:.2f}%** | +{tc['subcategory_classification']['improvement_f1']*100:.2f}% |
| **Priority Classification** | {tc['priority_classification']['v1_0_macro_f1']*100:.2f}% | **{tc['priority_classification']['v1_1_macro_f1']*100:.2f}%** | {tc['priority_classification']['v1_0_accuracy']*100:.2f}% | **{tc['priority_classification']['v1_1_accuracy']*100:.2f}%** | +{tc['priority_classification']['improvement_f1']*100:.2f}% |
| **Severity Classification** | {tc['severity_classification']['v1_0_macro_f1']*100:.2f}% | **{tc['severity_classification']['v1_1_macro_f1']*100:.2f}%** | {tc['severity_classification']['v1_0_accuracy']*100:.2f}% | **{tc['severity_classification']['v1_1_accuracy']*100:.2f}%** | +{tc['severity_classification']['improvement_f1']*100:.2f}% |

---

## 2. Calibration & Probability Quality (ECE)

* **v1.0 Expected Calibration Error (ECE)**: `{tc['calibration_ece']['v1_0_ece']:.4f}`
* **v1.1 Expected Calibration Error (ECE)**: `{tc['calibration_ece']['v1_1_ece']:.4f}`
* **ECE Reduction (Calibration Gain)**: **`-{tc['calibration_ece']['ece_reduction']:.4f}`** (lower is better)

---

## 3. Multilingual Breakdown (Category Macro F1)

| Language / Script | Samples | v1.0 Macro F1 | v1.1 Macro F1 | Improvement |
| :--- | :---: | :---: | :---: | :---: |
"""
    for lang, data in lb.items():
        md += f"| **{lang.upper()}** | {data['samples']} | {data['v1_0_f1']*100:.2f}% | **{data['v1_1_f1']*100:.2f}%** | +{data['improvement']*100:.2f}% |\n"

    md += f"""
---

## 4. Adversarial Challenge Set Benchmark (750 Slices)

| Challenge Group | Samples | v1.0 Cat Acc | v1.1 Cat Acc | v1.0 Griev Acc | v1.1 Griev Acc |
| :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for grp, sdata in cs.items():
        md += f"| **{grp}** | {sdata['samples']} | {sdata['v1_0_category_acc']*100:.2f}% | **{sdata['v1_1_category_acc']*100:.2f}%** | {sdata['v1_0_grievance_acc']*100:.2f}% | **{sdata['v1_1_grievance_acc']*100:.2f}%** |\n"

    md += f"""
---

## 5. Overall Challenge Set Accuracy

* **Category Accuracy**: {co['v1_0_category_acc']*100:.2f}% (v1.0) $\\rightarrow$ **{co['v1_1_category_acc']*100:.2f}% (v1.1)**
* **Grievance Accuracy**: {co['v1_0_grievance_acc']*100:.2f}% (v1.0) $\\rightarrow$ **{co['v1_1_grievance_acc']*100:.2f}% (v1.1)**
* **Priority Accuracy**: {co['v1_0_priority_acc']*100:.2f}% (v1.0) $\\rightarrow$ **{co['v1_1_priority_acc']*100:.2f}% (v1.1)**
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-v1-dir", type=str, default="models/grievance/v1")
    parser.add_argument("--model-v1-1-dir", type=str, default="models/grievance/v1.1")
    parser.add_argument("--test-path", type=str, default="data/test.json")
    parser.add_argument("--challenge-path", type=str, default="data/challenge.json")
    parser.add_argument("--artifacts-dir", type=str, default="artifacts/evaluation")
    args = parser.parse_args()

    run_comparative_evaluation(
        model_v1_dir=args.model_v1_dir,
        model_v1_1_dir=args.model_v1_1_dir,
        test_path=args.test_path,
        challenge_path=args.challenge_path,
        artifacts_dir=args.artifacts_dir,
    )
