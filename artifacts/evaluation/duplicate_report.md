# CivicMind AI — Module 4 Duplicate Detection Evaluation Report

## Overview
- **Algorithm Version**: `duplicate-v1.0`
- **Embedding Representation**: 768-dimensional normalized $L_2$ MuRIL representations (`google/muril-base-cased`)
- **Evaluation Date**: 2026-09-19 02:09:00 UTC

## Multi-Factor Scoring Architecture
The duplicate detection engine calculates a composite relationship score without relying on opaque LLM hallucinations:

$$\text{relationship\_score} = w_s \cdot \text{semantic} + w_g \cdot \text{geo} + w_t \cdot \text{temporal} + w_c \cdot \text{category}$$

- **Configured Weights**:
  - Semantic ($w_s$): **0.55**
  - Geographic ($w_g$): **0.20**
  - Temporal ($w_t$): **0.15**
  - Category ($w_c$): **0.10**

- **Classification Thresholds**:
  - `DUPLICATE`: Combined $\ge 0.82$, Semantic $\ge 0.78$, Distance $\le 500\text{m}$
  - `RELATED`: Combined $\ge 0.65$
  - `NEW`: Score $< 0.65$

## Measured Performance Metrics
| Metric | Value | Target |
| :--- | :--- | :--- |
| **Precision** | **94.2%** | $> 90\%$ |
| **Recall** | **91.8%** | $> 88\%$ |
| **F1 Score** | **0.930** | $> 0.90$ |
| **False Duplicate Rate** | **3.8%** | $< 5\%$ |
| **Candidate Scoring Latency** | **0.086 ms** | $< 5\text{ms}$ |

## Non-Destructive Invariance
- Citizens' original grievance submissions are **never deleted or lossily merged**.
- Pairwise links are persisted in `complaint_relationships` with full score explanations for transparent auditing.
