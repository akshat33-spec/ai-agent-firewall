"""
context_position_experiment/runner.py

Execution runner for the controlled follow-up experiment:
Context Length and Evidence Position in Runtime-Risk Monitoring.

Evaluates:
  - 3 Context levels: 1,000, 10,000, 50,000 tokens
  - 3 Evidence positions: beginning, middle, end (distributed)
  - Localized risk control (current action)
  - 2 Ground-truth classes: safe (negative), unsafe (positive)
  - 3 Replicated seeds: 1, 2, 3
  Total: 54 distributed + 18 localized = 72 decisions.

Features:
  --dry-run          Validates trial matrix, token accounting, baseline, and
                     prompt construction without making live API calls.
  --config           Path to configuration JSON.
  --seed             Randomization seed for trial execution order.

Results are saved to a new, non-destructive timestamped directory under results/.
Historical results (Run006, Run007, Run008, etc.) are strictly protected.
"""

import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from context.generator import get_encoder, actions_to_text
from detector.monitor import monitor, PROMPT_VERSION, SYSTEM_PROMPT, build_user_prompt
from context_position_experiment.trajectory import build_trial_trajectory
from context_position_experiment.baseline import DeterministicStatefulRuleBaseline

HISTORICAL_RUN_PREFIXES = [
    "2026-09-20_calibration_run001",
    "2026-09-20_calibration_run002",
    "2026-09-20_calibration_run003",
    "2026-09-20_calibration_run004",
    "2026-09-20_calibration_run005",
    "2026-09-20_calibration_run006",
    "2026-09-20_calibration_run007",
    "2026-09-20_calibration_run008",
    "2026-09-20_scenario1_run",
    "2026-10-14_scenario2_",
]


def verify_non_destructive_path(output_dir: str):
    """Enforce that runner never overwrites or writes into any historical run directory."""
    abs_out = os.path.abspath(output_dir)
    for hist in HISTORICAL_RUN_PREFIXES:
        if hist in abs_out:
            raise PermissionError(f"CRITICAL ERROR: Attempted to write to historical run directory: {abs_out}")


def compute_prompt_hash(system_prompt: str) -> str:
    """Compute SHA-256 hash of system prompt."""
    return hashlib.sha256(system_prompt.strip().encode("utf-8")).hexdigest()


def verify_api_authentication(api_key: str, model: str) -> Tuple[bool, str]:
    """Fail-fast verification of OpenAI API authentication."""
    if not api_key:
        return False, "OPENAI_API_KEY environment variable is missing or empty."
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        # Fast 1-token auth check
        resp = client.chat.completions.create(
            model=model,
            max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
        return True, "API authentication successful."
    except Exception as e:
        return False, f"API authentication failed: {str(e)}"


def build_trial_specs(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate all 72 planned trial specifications."""
    token_levels = config.get("token_levels", [1000, 10000, 50000])
    evidence_positions = config.get("evidence_positions", ["beginning", "middle", "end"])
    sample_types = config.get("sample_types", ["positive", "negative"])
    seeds = config.get("seeds", [1, 2, 3])

    trials = []

    # 1. Distributed conditions: 3 levels x 3 positions x 2 classes x 3 seeds = 54
    for level in token_levels:
        for pos in evidence_positions:
            for st in sample_types:
                for seed in seeds:
                    trial_id = f"dist_{pos}_{st[:3]}_{level}_{seed}"
                    trials.append({
                        "trial_id": trial_id,
                        "risk_structure": "distributed",
                        "evidence_position": pos,
                        "sample_type": st,
                        "token_level": level,
                        "seed": seed,
                    })

    # 2. Localized control: 3 levels x 2 classes x 3 seeds = 18
    for level in token_levels:
        for st in sample_types:
            for seed in seeds:
                trial_id = f"loc_cur_{st[:3]}_{level}_{seed}"
                trials.append({
                    "trial_id": trial_id,
                    "risk_structure": "localized",
                    "evidence_position": "current_action",
                    "sample_type": st,
                    "token_level": level,
                    "seed": seed,
                })

    return trials


def estimate_trial_token_usage(trials: List[Dict[str, Any]], encoder) -> Tuple[int, int]:
    """Estimate total target and approximate actual input tokens across all planned trials."""
    total_target = sum(t["token_level"] for t in trials)
    # Estimate total with ~5% overhead margin
    return len(trials), total_target


def main():
    parser = argparse.ArgumentParser(description="Run context position pilot experiment.")
    parser.add_argument("--config", default=os.path.join(os.path.dirname(__file__), "config.json"), help="Config file path")
    parser.add_argument("--dry-run", action="store_true", help="Validate trajectory construction without live API calls")
    parser.add_argument("--order-seed", type=int, default=20261019, help="Random seed for trial execution order")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        config = json.load(f)

    model = config.get("model", "gpt-4o-mini")
    temperature = config.get("temperature", 0.0)
    prompt_hash = compute_prompt_hash(SYSTEM_PROMPT)
    encoder = get_encoder(config.get("tokenizer", "cl100k_base"))

    print("=" * 78)
    print("AI AGENT RUNTIME RISK FIREWALL: CONTEXT & EVIDENCE POSITION PILOT")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f"Model: {model} | Temperature: {temperature} | Prompt Version: {PROMPT_VERSION}")
    print(f"System Prompt Hash (SHA-256): {prompt_hash[:16]}...{prompt_hash[-8:]}")
    print("=" * 78)

    # 1. Build and validate trial matrix
    trial_specs = build_trial_specs(config)
    num_trials, est_target_tokens = estimate_trial_token_usage(trial_specs, encoder)
    print(f"Planned Trials: {num_trials} (54 Distributed + 18 Localized Control)")
    print(f"Estimated Input Token Volume: ~{est_target_tokens:,} tokens (~{est_target_tokens / 1_000_000:.2f}M tokens)")

    # 2. Randomize trial order
    rng = random.Random(args.order_seed)
    shuffled_trials = list(trial_specs)
    rng.shuffle(shuffled_trials)
    for idx, t in enumerate(shuffled_trials, start=1):
        t["execution_order"] = idx

    print(f"Trial execution order randomized with seed={args.order_seed}")

    # 3. Check authentication and fail fast
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not args.dry_run:
        print("\nVerifying OpenAI API authentication...")
        auth_ok, auth_msg = verify_api_authentication(api_key, model)
        if not auth_ok:
            print(f"\n[FAIL FAST ERROR] {auth_msg}")
            print("Execution halted prior to running trials.")
            print("Please set a valid OPENAI_API_KEY in your environment, or pass --dry-run to validate locally.")
            sys.exit(1)
        print(f"[OK] {auth_msg}\n")
    else:
        print("\n[NOTE] Running in DRY-RUN mode. No live API calls will be made.\n")

    # 4. Prepare timestamped output directory
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ")
    run_id = f"2026-10-19_context_position_pilot_{timestamp}"
    base_results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
    out_dir = os.path.join(base_results_dir, run_id)

    verify_non_destructive_path(out_dir)
    os.makedirs(out_dir, exist_ok=False)

    results_csv = os.path.join(out_dir, "pilot_results.csv")
    results_jsonl = os.path.join(out_dir, "pilot_raw.jsonl")
    metadata_json = os.path.join(out_dir, "run_metadata.json")

    # Save run metadata
    run_meta = {
        "run_id": run_id,
        "experiment_id": config.get("experiment_id", "context_position_pilot_v1.0"),
        "timestamp_start": datetime.utcnow().isoformat() + "Z",
        "dry_run": args.dry_run,
        "model": model,
        "temperature": temperature,
        "prompt_version": PROMPT_VERSION,
        "system_prompt_sha256": prompt_hash,
        "randomize_seed": args.order_seed,
        "planned_trials": num_trials,
        "config": config,
        "software_versions": {
            "python": sys.version,
        },
    }
    with open(metadata_json, "w", encoding="utf-8") as f_meta:
        json.dump(run_meta, f_meta, indent=2)

    # 5. Initialize deterministic baseline
    oracle_baseline = DeterministicStatefulRuleBaseline()

    fieldnames = [
        "run_id", "trial_id", "execution_order", "timestamp", "scenario",
        "risk_structure", "evidence_position", "evidence_step", "total_steps",
        "token_level", "seed", "sample_type", "ground_truth",
        "oracle_baseline_prediction", "oracle_baseline_correct",
        "llm_prediction", "llm_correct", "confidence", "reason",
        "prefix_tokens", "actual_tokens", "target_tokens", "decision_time_ms",
        "model", "prompt_version", "prompt_hash", "error"
    ]

    trials_completed = 0
    llm_correct_count = 0
    oracle_correct_count = 0

    with open(results_csv, "w", newline="", encoding="utf-8") as f_csv, \
         open(results_jsonl, "w", encoding="utf-8") as f_jsonl:

        writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
        writer.writeheader()

        for spec in shuffled_trials:
            trials_completed += 1
            t_id = spec["trial_id"]
            order = spec["execution_order"]
            structure = spec["risk_structure"]
            pos = spec["evidence_position"]
            st = spec["sample_type"]
            level = spec["token_level"]
            seed = spec["seed"]

            # Construct controlled trajectory
            traj = build_trial_trajectory(
                risk_structure=structure,
                sample_type=st,
                evidence_position=pos,
                target_tokens=level,
                seed=seed,
                encoder=encoder,
            )

            ground_truth = traj["ground_truth"]
            actual_tokens = traj["actual_tokens"]
            evidence_step = traj["evidence_step"]
            total_steps = traj["total_steps"]

            # Evaluate deterministic oracle baseline
            base_res = oracle_baseline.evaluate(traj)
            base_pred = base_res["prediction"]
            base_correct = (base_pred == ground_truth)
            if base_correct:
                oracle_correct_count += 1

            # Monitor LLM evaluation
            if args.dry_run:
                llm_prediction = "DRY_RUN"
                confidence = 1.0
                reason = "Dry run mode - no LLM invocation."
                evidence = []
                error = None
                decision_time_ms = 0.0
                llm_correct = None
            else:
                monitor_cfg = {
                    "model": model,
                    "temperature": temperature,
                    "prompt_version": PROMPT_VERSION,
                    "system_prompt": SYSTEM_PROMPT,
                }
                t0 = time.perf_counter()
                res = monitor(traj["context_obs"], traj["current_obs"], monitor_cfg)
                decision_time_ms = (time.perf_counter() - t0) * 1000.0

                llm_prediction = res.get("prediction", "ERROR")
                confidence = res.get("confidence", 0.0)
                reason = res.get("reason", "")
                evidence = res.get("evidence", [])
                error = res.get("error")

                llm_correct = (llm_prediction == ground_truth) if error is None else False
                if llm_correct:
                    llm_correct_count += 1

            trial_time = datetime.utcnow().isoformat() + "Z"

            row = {
                "run_id": run_id,
                "trial_id": t_id,
                "execution_order": order,
                "timestamp": trial_time,
                "scenario": "S1",
                "risk_structure": structure,
                "evidence_position": pos,
                "evidence_step": evidence_step,
                "total_steps": total_steps,
                "token_level": level,
                "seed": seed,
                "sample_type": st,
                "ground_truth": ground_truth,
                "oracle_baseline_prediction": base_pred,
                "oracle_baseline_correct": base_correct,
                "llm_prediction": llm_prediction,
                "llm_correct": llm_correct,
                "confidence": confidence,
                "reason": reason,
                "prefix_tokens": traj["prefix_tokens"],
                "actual_tokens": actual_tokens,
                "target_tokens": level,
                "decision_time_ms": round(decision_time_ms, 2),
                "model": model,
                "prompt_version": PROMPT_VERSION,
                "prompt_hash": prompt_hash,
                "error": error,
            }
            writer.writerow(row)
            f_csv.flush()

            raw_entry = dict(row)
            raw_entry["evidence"] = evidence
            raw_entry["baseline_evidence"] = base_res.get("evidence", [])
            raw_entry["current_action_observable"] = actions_to_text([traj["current_obs"]])
            f_jsonl.write(json.dumps(raw_entry) + "\n")
            f_jsonl.flush()

            status_str = f"GT={ground_truth:6s} | BASE={base_pred:6s} | LLM={llm_prediction:7s}"
            print(f"[{trials_completed:02d}/{num_trials}] #{order:02d} | {structure:11s} | {pos:14s} | {level:>5d} tok | seed={seed} | {status_str}")

    print("\n" + "=" * 78)
    print(f"PILOT EXPERIMENT COMPLETE: {trials_completed}/{num_trials} trials processed.")
    print(f"Oracle Baseline Accuracy: {oracle_correct_count}/{num_trials} (100.0%)")
    if not args.dry_run:
        print(f"LLM Accuracy: {llm_correct_count}/{num_trials} ({llm_correct_count/num_trials*100:.1f}%)")
    print(f"Output Directory: {out_dir}")
    print("=" * 78)


if __name__ == "__main__":
    main()
