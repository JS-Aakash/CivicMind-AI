# CivicMind AI — MuRIL v1.0 vs MuRIL v1.1 Comparative Evaluation Report

**Generated**: 2026-09-19T01:22:36Z
**Hardware Device**: NVIDIA GeForce RTX 3050 6GB Laptop GPU
**Test Set Size**: 1494 samples (100% UNTOUCHED)
**Challenge Set Size**: 750 samples (100% UNTOUCHED)

---

## 1. Executive Summary & Core Task Metrics (Standard Test Set)

| Task Head | v1.0 Macro F1 | v1.1 Macro F1 | v1.0 Accuracy | v1.1 Accuracy | $\Delta$ F1 Gain |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Grievance Detection** | 100.00% | **100.00%** | 100.00% | **100.00%** | +0.00% |
| **Primary Category** | 70.79% | **73.05%** | 78.11% | **77.84%** | +2.26% |
| **Subcategory (Hierarchical)** | 11.47% | **11.16%** | 19.95% | **20.08%** | +-0.31% |
| **Priority Classification** | 37.97% | **43.15%** | 54.02% | **56.02%** | +5.18% |
| **Severity Classification** | 49.86% | **54.00%** | 58.63% | **61.45%** | +4.14% |

---

## 2. Calibration & Probability Quality (ECE)

* **v1.0 Expected Calibration Error (ECE)**: `0.4767`
* **v1.1 Expected Calibration Error (ECE)**: `0.4211`
* **ECE Reduction (Calibration Gain)**: **`-0.0556`** (lower is better)

---

## 3. Multilingual Breakdown (Category Macro F1)

| Language / Script | Samples | v1.0 Macro F1 | v1.1 Macro F1 | Improvement |
| :--- | :---: | :---: | :---: | :---: |
| **EN** | 1494 | 70.79% | **73.05%** | +2.26% |

---

## 4. Adversarial Challenge Set Benchmark (750 Slices)

| Challenge Group | Samples | v1.0 Cat Acc | v1.1 Cat Acc | v1.0 Griev Acc | v1.1 Griev Acc |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **unknown** | 750 | 47.20% | **70.67%** | 94.13% | **100.00%** |

---

## 5. Overall Challenge Set Accuracy

* **Category Accuracy**: 47.20% (v1.0) $\rightarrow$ **70.67% (v1.1)**
* **Grievance Accuracy**: 94.13% (v1.0) $\rightarrow$ **100.00% (v1.1)**
* **Priority Accuracy**: 58.80% (v1.0) $\rightarrow$ **76.40% (v1.1)**
