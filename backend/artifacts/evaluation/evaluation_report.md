# CivicMind AI — Model Evaluation Report
## Model: MuRIL Multi-Task Grievance Intelligence (Version: v1.0)

### 1. Overall Task Performance (Test Set: 1494 examples)
| Task | Accuracy | Macro F1 | Weighted F1 |
|---|---|---|---|
| **Grievance Detection** | 100.0% | 1.0000 | 1.0000 |
| **Category Classification (10 classes)** | 78.1% | 0.7079 | 0.7961 |
| **Priority Routing (4 classes)** | 54.0% | 0.3797 | 0.4189 |
| **Severity Assessment (4 classes)** | 58.6% | 0.4986 | 0.5619 |

### 2. Per-Language & Dialect Breakdown
| Dialect Profile | Samples | Category Acc | Category F1 | Priority F1 | Grievance F1 |
|---|---|---|---|---|---|
| **hi_code_mixed** | 417 | 74.3% | 0.7762 | 0.4213 | 1.0000 |
| **ta_code_mixed** | 459 | 78.6% | 0.7983 | 0.4045 | 1.0000 |
| **hi** | 212 | 76.9% | 0.7698 | 0.4821 | 1.0000 |
| **en** | 213 | 82.2% | 0.8169 | 0.3651 | 1.0000 |
| **ta** | 193 | 81.9% | 0.8268 | 0.4349 | 1.0000 |

### 3. Challenge Dataset Results (750 Hard/Edge Examples)
- **Category Accuracy**: 47.2%
- **Macro F1**: 0.2602

### 4. Error Analysis Summary
- Total test classification discrepancies: 1494
- Top 100 discrepancies saved in `artifacts/evaluation/error_analysis.json`
