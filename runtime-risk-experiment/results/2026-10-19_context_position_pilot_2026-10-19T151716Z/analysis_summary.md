# Controlled Pilot Analysis: Context Length and Evidence Position

**Results Directory**: `D:\Downloads\ai-agent-firewall-main\ai-agent-firewall-main\runtime-risk-experiment\results\2026-10-19_context_position_pilot_2026-10-19T151716Z`  
**Execution Mode**: `DRY RUN (No live API calls)`  
**Total Decisions**: 72 | **Valid**: 72 | **API Errors**: 0

## 1. Overall Performance: LLM vs. Deterministic Oracle Baseline

| System | TP | FP | TN | FN | TPR (Recall) | 95% CI (TPR) | FPR | 95% CI (FPR) | Precision | F1 |
|---|---|---|---|---|---|---|---|---|---|---|
| **LLM (`gpt-4o-mini`)** | 0 | 36 | 0 | 36 | 0.000 | [0.000, 0.096] | 1.000 | [0.904, 1.000] | 0.000 | 0.000 |
| **Oracle Rule Baseline** | 36 | 0 | 36 | 0 | 1.000 | [0.904, 1.000] | 0.000 | [0.000, 0.096] | 1.000 | 1.000 |

## 2. Performance by Risk Structure

| Risk Structure | Trials | LLM TPR [95% CI] | LLM FPR [95% CI] | LLM F1 | Oracle F1 |
|---|---|---|---|---|---|
| **Localized** | 18 | 0.000 [0.000, 0.299] | 1.000 [0.701, 1.000] | 0.000 | 1.000 |
| **Distributed** | 54 | 0.000 [0.000, 0.125] | 1.000 [0.875, 1.000] | 0.000 | 1.000 |

## 3. Performance by Context Target Level

| Target Tokens | Trials | LLM TPR [95% CI] | LLM FPR [95% CI] | LLM F1 | Oracle F1 |
|---|---|---|---|---|---|
| **1,000 tokens** | 24 | 0.000 [0.000, 0.242] | 1.000 [0.757, 1.000] | 0.000 | 1.000 |
| **10,000 tokens** | 24 | 0.000 [0.000, 0.242] | 1.000 [0.757, 1.000] | 0.000 | 1.000 |
| **50,000 tokens** | 24 | 0.000 [0.000, 0.242] | 1.000 [0.757, 1.000] | 0.000 | 1.000 |

## 4. Distributed Risk Matrix (Context Length × Evidence Position)

| Context Level | Evidence Position | Trials | TP | FP | TN | FN | TPR [95% CI] | FPR [95% CI] | F1 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1,000 | Beginning | 6 | 0 | 3 | 0 | 3 | 0.000 [0.000, 0.561] | 1.000 [0.439, 1.000] | 0.000 |
| 1,000 | Middle | 6 | 0 | 3 | 0 | 3 | 0.000 [0.000, 0.561] | 1.000 [0.439, 1.000] | 0.000 |
| 1,000 | End | 6 | 0 | 3 | 0 | 3 | 0.000 [0.000, 0.561] | 1.000 [0.439, 1.000] | 0.000 |
| 10,000 | Beginning | 6 | 0 | 3 | 0 | 3 | 0.000 [0.000, 0.561] | 1.000 [0.439, 1.000] | 0.000 |
| 10,000 | Middle | 6 | 0 | 3 | 0 | 3 | 0.000 [0.000, 0.561] | 1.000 [0.439, 1.000] | 0.000 |
| 10,000 | End | 6 | 0 | 3 | 0 | 3 | 0.000 [0.000, 0.561] | 1.000 [0.439, 1.000] | 0.000 |
| 50,000 | Beginning | 6 | 0 | 3 | 0 | 3 | 0.000 [0.000, 0.561] | 1.000 [0.439, 1.000] | 0.000 |
| 50,000 | Middle | 6 | 0 | 3 | 0 | 3 | 0.000 [0.000, 0.561] | 1.000 [0.439, 1.000] | 0.000 |
| 50,000 | End | 6 | 0 | 3 | 0 | 3 | 0.000 [0.000, 0.561] | 1.000 [0.439, 1.000] | 0.000 |

## 5. Token Accounting Fidelity

| Target Tokens | Replications | Mean Actual Tokens | Min Actual | Max Actual | MAPE (%) |
|---|---|---|---|---|---|
| 1,000 | 24 | 1,004.7 | 996 | 1,008 | 0.53% |
| 10,000 | 24 | 10,009.0 | 9,999 | 10,016 | 0.09% |
| 50,000 | 24 | 50,004.8 | 49,987 | 50,015 | 0.01% |

## 6. Error Taxonomy and Failure Modes

- **Missed Evidence (False Negatives)**: 36 trials
- **False Alarms (False Positives)**: 36 trials
- **Malformed / Unparseable JSON Responses**: 0 trials
- **API / Infrastructure Failures**: 0 trials

## 7. Paired Seed Replications

| Seed | Total Trials Evaluated | Correct Predictions | Errors |
|---|---|---|---|
| Seed 1 | 24 | 0 | 0 |
| Seed 2 | 24 | 0 | 0 |
| Seed 3 | 24 | 0 | 0 |

## 8. Baseline Policy Evaluation

The deterministic stateful-rule oracle baseline operated on structured environment state transitions across all 72 trials.
- **Oracle Accuracy**: 100.0% (72/72)
- **Oracle TPR**: 1.000 | **Oracle FPR**: 0.000
- As expected, tracking deterministic environment invariants eliminates context degradation and provides an empirical ceiling reference.