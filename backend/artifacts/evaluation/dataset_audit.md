# CivicMind AI — Dataset & Model Implementation Audit (Module 2.5)

## 1. Overall Dataset Overview
- **Total Standard Samples**: 14,917
- **Train Split**: 11,937 (80.0%)
- **Validation Split**: 1,486 (10.0%)
- **Test Split**: 1,494 (10.0%)
- **Challenge Set (Hard/Edge)**: 750 (Isolated evaluation set)

## 2. Scenario-Level Leakage Check
- **Train Scenarios**: 2,340
- **Val Scenarios**: 292
- **Test Scenarios**: 294
- **Train ∩ Val Overlap**: `0`
- **Train ∩ Test Overlap**: `0`
- **Val ∩ Test Overlap**: `0`
- **Leak-Free Status**: `✅ PASS (Zero Leakage)`

## 3. Language & Dialect Distribution
| Language Code | Sample Count | Percentage |
|---|---|---|
| `ta` | 6,477 | 43.4% |
| `hi` | 6,283 | 42.1% |
| `en` | 2,157 | 14.5% |

## 4. Class Distribution Across Core Tasks

### A. Grievance Status
- **Genuine Grievances (`True`)**: 13,103 (87.8%)
- **Non-Grievance Inquiries (`False`)**: 1,814 (12.2%)

### B. Priority Distribution
| Priority Tier | Samples | Percentage |
|---|---|---|
| `low` | 2,519 | 16.9% |
| `medium` | 3,215 | 21.6% |
| `high` | 6,205 | 41.6% |
| `critical` | 2,978 | 20.0% |

### C. Category Distribution (10 Core Classes)
| Category | Samples | Percentage |
|---|---|---|
| `water` | 2,974 | 19.9% |
| `roads` | 2,492 | 16.7% |
| `sanitation` | 1,777 | 11.9% |
| `electricity` | 2,065 | 13.8% |
| `transport` | 1,378 | 9.2% |
| `healthcare` | 1,370 | 9.2% |
| `drainage` | 1,122 | 7.5% |
| `street_infrastructure` | 739 | 5.0% |
| `public_safety` | 744 | 5.0% |
| `other` | 256 | 1.7% |

## 5. Short-Text Vulnerability Analysis
- **Short Complaints (≤ 4 words)**: `0` (0.00%)
- **Average Word Count**: `17.02` words
- **Range**: `6` to `30` words
- **Diagnosis**: Ultra-short citizen complaints (e.g., *"thanni varala"*, *"paani nahi aa raha"*, *"road damage"*) are severely underrepresented (< 2% of the dataset). Because MuRIL uses subword WordPiece tokenization, short romanized phrases lack sufficient token mass compared to standard sentences, leading to category ambiguity.

## 6. Multi-Issue and Compound Findings
- In v1.0, training data enforced strict single-label cross-entropy.
- Complex complaints mentioning multiple hazards (e.g., *"Road damaged and rain water collecting"* or *"Live wire fallen on road"*) create label competition between `roads` and `water`/`electricity`.
- An additive multi-label issue head is required.

## 7. Probability Calibration Deficit
- v1.0 outputs raw uncalibrated softmax logits. Across 10 categories, probability mass dilutes into neighboring categories (~30%–45%), even when the primary category is correct.
- Temperature scaling learned strictly on the validation set is required to calculate Expected Calibration Error (ECE) and calibrate probability bands.
