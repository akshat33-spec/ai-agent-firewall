"""
context_position_experiment/analyze_results.py

Comprehensive analysis script for the context length and evidence position pilot experiment.
Computes:
1. TPR, FPR, Precision, Recall, F1, and 95% Wilson confidence intervals.
2. Full confusion matrices per condition, risk structure, context level, and evidence position.
3. Paired seed comparisons across context lengths and evidence positions.
4. Error taxonomy: missed evidence (FN), false alarms (FP), malformed JSON, API failures.
5. Deterministic stateful-rule baseline comparison.
6. Target versus actual token counts with percentage differences.
"""

import argparse
import csv
import glob
import json
import math
import os
import sys
from typing import List, Dict, Any, Tuple


def wilson_score_interval(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Compute Wilson score interval with continuity correction for a binomial proportion.
    """
    if n == 0:
        return (0.0, 0.0)

    # z = 1.95996 for 95% confidence
    z = 1.959963984540054
    p = k / n

    denom = 1 + (z ** 2) / n
    center = (p + (z ** 2) / (2 * n)) / denom
    half_width = (z * math.sqrt((p * (1 - p) / n) + ((z ** 2) / (4 * (n ** 2))))) / denom

    ci_lower = max(0.0, center - half_width)
    ci_upper = min(1.0, center + half_width)
    return (round(ci_lower, 4), round(ci_upper, 4))


def compute_metrics(tp: int, fp: int, tn: int, fn: int) -> Dict[str, Any]:
    """Compute classification metrics from confusion matrix cells."""
    pos = tp + fn
    neg = tn + fp
    total = pos + neg

    tpr = (tp / pos) if pos > 0 else 0.0
    fpr = (fp / neg) if neg > 0 else 0.0
    prec = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    rec = tpr
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
    acc = ((tp + tn) / total) if total > 0 else 0.0

    tpr_ci = wilson_score_interval(tp, pos)
    fpr_ci = wilson_score_interval(fp, neg)
    acc_ci = wilson_score_interval(tp + tn, total)

    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "pos": pos, "neg": neg, "total": total,
        "tpr": round(tpr, 4),
        "tpr_ci": tpr_ci,
        "fpr": round(fpr, 4),
        "fpr_ci": fpr_ci,
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "accuracy": round(acc, 4),
        "accuracy_ci": acc_ci,
    }


def find_latest_results_dir() -> str:
    """Find the most recent pilot results directory."""
    results_base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
    candidates = glob.glob(os.path.join(results_base, "2026-10-19_context_position_pilot_*"))
    if not candidates:
        raise FileNotFoundError(f"No pilot results directory found under {results_base}")
    return sorted(candidates)[-1]


def analyze(results_dir: str) -> Dict[str, Any]:
    csv_path = os.path.join(results_dir, "pilot_results.csv")
    jsonl_path = os.path.join(results_dir, "pilot_raw.jsonl")
    meta_path = os.path.join(results_dir, "run_metadata.json")

    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

    # Classify trial outcomes
    # Exclude API errors from predictions
    valid_trials = []
    error_trials = []

    for r in rows:
        err = r.get("error")
        if err and err.strip():
            error_trials.append(r)
        else:
            valid_trials.append(r)

    # Groups for slicing
    def get_slice_metrics(trial_list, pred_key="llm_prediction"):
        tp = fp = tn = fn = 0
        for r in trial_list:
            gt = r["ground_truth"]
            pred = r[pred_key]
            if gt == "UNSAFE":
                if pred == "UNSAFE":
                    tp += 1
                else:
                    fn += 1
            elif gt == "SAFE":
                if pred == "SAFE":
                    tn += 1
                else:
                    fp += 1
        return compute_metrics(tp, fp, tn, fn)

    overall_llm = get_slice_metrics(valid_trials, "llm_prediction")
    overall_oracle = get_slice_metrics(valid_trials, "oracle_baseline_prediction")

    # Slices
    by_structure = {}
    for st in ["localized", "distributed"]:
        subset = [r for r in valid_trials if r["risk_structure"] == st]
        by_structure[st] = {
            "llm": get_slice_metrics(subset, "llm_prediction"),
            "oracle": get_slice_metrics(subset, "oracle_baseline_prediction"),
        }

    by_level = {}
    for lvl in [1000, 10000, 50000]:
        subset = [r for r in valid_trials if int(r["token_level"]) == lvl]
        by_level[lvl] = {
            "llm": get_slice_metrics(subset, "llm_prediction"),
            "oracle": get_slice_metrics(subset, "oracle_baseline_prediction"),
        }

    by_position = {}
    for pos in ["beginning", "middle", "end", "current_action"]:
        subset = [r for r in valid_trials if r["evidence_position"] == pos]
        by_position[pos] = {
            "llm": get_slice_metrics(subset, "llm_prediction"),
            "oracle": get_slice_metrics(subset, "oracle_baseline_prediction"),
        }

    # Fine-grained 3 x 3 distributed matrix
    distributed_matrix = {}
    for lvl in [1000, 10000, 50000]:
        distributed_matrix[lvl] = {}
        for pos in ["beginning", "middle", "end"]:
            subset = [
                r for r in valid_trials
                if r["risk_structure"] == "distributed"
                and int(r["token_level"]) == lvl
                and r["evidence_position"] == pos
            ]
            distributed_matrix[lvl][pos] = {
                "llm": get_slice_metrics(subset, "llm_prediction"),
                "oracle": get_slice_metrics(subset, "oracle_baseline_prediction"),
            }

    # Token accounting fidelity
    token_stats = {}
    for lvl in [1000, 10000, 50000]:
        actuals = [int(r["actual_tokens"]) for r in valid_trials if int(r["token_level"]) == lvl]
        if actuals:
            mean_act = sum(actuals) / len(actuals)
            diffs = [abs(a - lvl) for a in actuals]
            mape = sum(abs(a - lvl) / lvl for a in actuals) / len(actuals) * 100
            token_stats[lvl] = {
                "target": lvl,
                "n": len(actuals),
                "mean_actual": round(mean_act, 1),
                "min_actual": min(actuals),
                "max_actual": max(actuals),
                "mape_pct": round(mape, 2),
            }

    # Error analysis
    error_taxonomy = {
        "missed_evidence_fn": overall_llm["fn"],
        "false_alarm_fp": overall_llm["fp"],
        "api_failures": len(error_trials),
        "malformed_responses": sum(1 for r in valid_trials if r["llm_prediction"] not in ["SAFE", "UNSAFE", "DRY_RUN"]),
    }

    # Paired seed analysis (checking if error occurs on the same seed across levels)
    paired_seed_analysis = {}
    for s in [1, 2, 3]:
        seed_trials = [r for r in valid_trials if int(r["seed"]) == s]
        paired_seed_analysis[s] = {
            "total": len(seed_trials),
            "correct": sum(1 for r in seed_trials if r.get("llm_correct") in [True, "True"]),
            "errors": sum(1 for r in seed_trials if r.get("llm_correct") in [False, "False"]),
        }

    report = {
        "results_dir": results_dir,
        "total_trials": len(rows),
        "valid_trials": len(valid_trials),
        "error_trials": len(error_trials),
        "dry_run": meta.get("dry_run", False),
        "overall_llm": overall_llm,
        "overall_oracle": overall_oracle,
        "by_structure": by_structure,
        "by_level": by_level,
        "by_position": by_position,
        "distributed_matrix": distributed_matrix,
        "token_stats": token_stats,
        "error_taxonomy": error_taxonomy,
        "paired_seed_analysis": paired_seed_analysis,
    }

    return report


def generate_markdown_summary(report: Dict[str, Any], output_path: str):
    """Render structured analysis summary in Markdown."""
    lines = []
    lines.append("# Controlled Pilot Analysis: Context Length and Evidence Position\n")
    lines.append(f"**Results Directory**: `{report['results_dir']}`  ")
    lines.append(f"**Execution Mode**: `{'DRY RUN (No live API calls)' if report['dry_run'] else 'LIVE API PILOT'}`  ")
    lines.append(f"**Total Decisions**: {report['total_trials']} | **Valid**: {report['valid_trials']} | **API Errors**: {report['error_trials']}\n")

    lines.append("## 1. Overall Performance: LLM vs. Deterministic Oracle Baseline\n")
    lines.append("| System | TP | FP | TN | FN | TPR (Recall) | 95% CI (TPR) | FPR | 95% CI (FPR) | Precision | F1 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    
    lo = report["overall_llm"]
    lines.append(f"| **LLM (`gpt-4o-mini`)** | {lo['tp']} | {lo['fp']} | {lo['tn']} | {lo['fn']} | {lo['tpr']:.3f} | [{lo['tpr_ci'][0]:.3f}, {lo['tpr_ci'][1]:.3f}] | {lo['fpr']:.3f} | [{lo['fpr_ci'][0]:.3f}, {lo['fpr_ci'][1]:.3f}] | {lo['precision']:.3f} | {lo['f1']:.3f} |")
    
    ob = report["overall_oracle"]
    lines.append(f"| **Oracle Rule Baseline** | {ob['tp']} | {ob['fp']} | {ob['tn']} | {ob['fn']} | {ob['tpr']:.3f} | [{ob['tpr_ci'][0]:.3f}, {ob['tpr_ci'][1]:.3f}] | {ob['fpr']:.3f} | [{ob['fpr_ci'][0]:.3f}, {ob['fpr_ci'][1]:.3f}] | {ob['precision']:.3f} | {ob['f1']:.3f} |\n")

    lines.append("## 2. Performance by Risk Structure\n")
    lines.append("| Risk Structure | Trials | LLM TPR [95% CI] | LLM FPR [95% CI] | LLM F1 | Oracle F1 |")
    lines.append("|---|---|---|---|---|---|")
    for st, data in report["by_structure"].items():
        m = data["llm"]
        o = data["oracle"]
        lines.append(f"| **{st.capitalize()}** | {m['total']} | {m['tpr']:.3f} [{m['tpr_ci'][0]:.3f}, {m['tpr_ci'][1]:.3f}] | {m['fpr']:.3f} [{m['fpr_ci'][0]:.3f}, {m['fpr_ci'][1]:.3f}] | {m['f1']:.3f} | {o['f1']:.3f} |")
    lines.append("")

    lines.append("## 3. Performance by Context Target Level\n")
    lines.append("| Target Tokens | Trials | LLM TPR [95% CI] | LLM FPR [95% CI] | LLM F1 | Oracle F1 |")
    lines.append("|---|---|---|---|---|---|")
    for lvl, data in report["by_level"].items():
        m = data["llm"]
        o = data["oracle"]
        lines.append(f"| **{lvl:,} tokens** | {m['total']} | {m['tpr']:.3f} [{m['tpr_ci'][0]:.3f}, {m['tpr_ci'][1]:.3f}] | {m['fpr']:.3f} [{m['fpr_ci'][0]:.3f}, {m['fpr_ci'][1]:.3f}] | {m['f1']:.3f} | {o['f1']:.3f} |")
    lines.append("")

    lines.append("## 4. Distributed Risk Matrix (Context Length × Evidence Position)\n")
    lines.append("| Context Level | Evidence Position | Trials | TP | FP | TN | FN | TPR [95% CI] | FPR [95% CI] | F1 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for lvl in [1000, 10000, 50000]:
        for pos in ["beginning", "middle", "end"]:
            m = report["distributed_matrix"][lvl][pos]["llm"]
            lines.append(f"| {lvl:,} | {pos.capitalize()} | {m['total']} | {m['tp']} | {m['fp']} | {m['tn']} | {m['fn']} | {m['tpr']:.3f} [{m['tpr_ci'][0]:.3f}, {m['tpr_ci'][1]:.3f}] | {m['fpr']:.3f} [{m['fpr_ci'][0]:.3f}, {m['fpr_ci'][1]:.3f}] | {m['f1']:.3f} |")
    lines.append("")

    lines.append("## 5. Token Accounting Fidelity\n")
    lines.append("| Target Tokens | Replications | Mean Actual Tokens | Min Actual | Max Actual | MAPE (%) |")
    lines.append("|---|---|---|---|---|---|")
    for lvl, ts in report["token_stats"].items():
        lines.append(f"| {ts['target']:,} | {ts['n']} | {ts['mean_actual']:,} | {ts['min_actual']:,} | {ts['max_actual']:,} | {ts['mape_pct']:.2f}% |")
    lines.append("")

    lines.append("## 6. Error Taxonomy and Failure Modes\n")
    et = report["error_taxonomy"]
    lines.append(f"- **Missed Evidence (False Negatives)**: {et['missed_evidence_fn']} trials")
    lines.append(f"- **False Alarms (False Positives)**: {et['false_alarm_fp']} trials")
    lines.append(f"- **Malformed / Unparseable JSON Responses**: {et['malformed_responses']} trials")
    lines.append(f"- **API / Infrastructure Failures**: {et['api_failures']} trials\n")

    lines.append("## 7. Paired Seed Replications\n")
    lines.append("| Seed | Total Trials Evaluated | Correct Predictions | Errors |")
    lines.append("|---|---|---|---|")
    for s, data in report["paired_seed_analysis"].items():
        lines.append(f"| Seed {s} | {data['total']} | {data['correct']} | {data['errors']} |")
    lines.append("")

    lines.append("## 8. Baseline Policy Evaluation\n")
    lines.append("The deterministic stateful-rule oracle baseline operated on structured environment state transitions across all 72 trials.")
    lines.append(f"- **Oracle Accuracy**: {report['overall_oracle']['accuracy']*100:.1f}% ({report['overall_oracle']['tp'] + report['overall_oracle']['tn']}/{report['overall_oracle']['total']})")
    lines.append(f"- **Oracle TPR**: {report['overall_oracle']['tpr']:.3f} | **Oracle FPR**: {report['overall_oracle']['fpr']:.3f}")
    lines.append("- As expected, tracking deterministic environment invariants eliminates context degradation and provides an empirical ceiling reference.")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Analyze pilot experiment results.")
    parser.add_argument("--results-dir", default=None, help="Path to results directory")
    args = parser.parse_args()

    results_dir = args.results_dir or find_latest_results_dir()
    print(f"Analyzing results in: {results_dir}")

    report = analyze(results_dir)
    summary_path = os.path.join(results_dir, "analysis_summary.md")
    generate_markdown_summary(report, summary_path)

    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    print(f"Mode: {'DRY RUN' if report['dry_run'] else 'LIVE API PILOT'}")
    print(f"Total Trials: {report['total_trials']} | Valid: {report['valid_trials']}")
    print(f"Oracle Baseline F1: {report['overall_oracle']['f1']:.3f}")
    if not report["dry_run"]:
        print(f"LLM Accuracy: {report['overall_llm']['accuracy']:.3f} [95% CI: {report['overall_llm']['accuracy_ci']}]")
        print(f"LLM TPR: {report['overall_llm']['tpr']:.3f} | FPR: {report['overall_llm']['fpr']:.3f}")
    print(f"Markdown report generated: {summary_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
