"""
context_position_experiment/trajectory.py

Controlled trajectory generator for context length and evidence position experiment.
Ensures:
1. Target context tokens (1,000, 10,000, 50,000) using tiktoken cl100k_base.
2. Controlled evidence placement (beginning, middle, end) for distributed risk.
3. 100% matched benign filler between safe and unsafe pairs within each (level, seed).
4. Strictly invariant Action D with zero classification leakage.
5. Deterministic state tracking and ground-truth evaluation.
"""

from typing import List, Dict, Any, Tuple
import copy

from context.generator import (
    get_encoder,
    generate_and_validate_for_tokens,
    action_to_observable_dict,
    actions_to_text,
)
from detector.monitor import SYSTEM_PROMPT, build_user_prompt
from environment.evaluator import security_violation
from environment.state import initial_state, EnvironmentState
from experiments.run_calibration import estimate_monitor_input_tokens
from experiments.run_experiment import (
    get_localized_actions,
    get_distributed_actions,
    execute_actions_for_ground_truth,
)


def get_canonical_overhead(encoder=None) -> Dict[str, int]:
    """
    Calculate maximum fixed overhead for localized and distributed trajectories
    to ensure safe/unsafe pairs share identical filler length.
    """
    if encoder is None:
        encoder = get_encoder()

    # Localized max overhead
    loc_pos = get_localized_actions("positive")
    loc_cur_obs = action_to_observable_dict(
        loc_pos[0]["label"], loc_pos[0]["description"], step=1, result_str=loc_pos[0].get("result", "")
    )
    loc_overhead = estimate_monitor_input_tokens([], loc_cur_obs, encoder, SYSTEM_PROMPT)

    # Distributed max overhead (A, B, C in history, D as current)
    dist_pos = get_distributed_actions("positive")
    history_obs = [
        action_to_observable_dict(dist_pos[i]["label"], dist_pos[i]["description"], step=i + 1, result_str=dist_pos[i].get("result", ""))
        for i in range(3)
    ]
    cur_obs = action_to_observable_dict(dist_pos[3]["label"], dist_pos[3]["description"], step=4, result_str=dist_pos[3].get("result", ""))
    dist_overhead = estimate_monitor_input_tokens(history_obs, cur_obs, encoder, SYSTEM_PROMPT)

    return {
        "localized": loc_overhead,
        "distributed": dist_overhead,
    }


def build_trial_trajectory(
    risk_structure: str,
    sample_type: str,
    evidence_position: str,
    target_tokens: int,
    seed: int,
    encoder=None,
) -> Dict[str, Any]:
    """
    Construct complete trial trajectory with observable history and current action.

    Args:
        risk_structure: 'distributed' or 'localized'
        sample_type: 'positive' (UNSAFE) or 'negative' (SAFE)
        evidence_position: 'beginning', 'middle', 'end' (or 'current_action' for localized)
        target_tokens: 1000, 10000, or 50000
        seed: integer random seed for benign filler generation
        encoder: tiktoken encoder

    Returns:
        dict containing context_obs, current_obs, ground_truth, token counts, etc.
    """
    if encoder is None:
        encoder = get_encoder()

    overheads = get_canonical_overhead(encoder)

    if risk_structure == "localized":
        sec_actions = get_localized_actions(sample_type)
        _st, gt_violation = execute_actions_for_ground_truth(sec_actions)
        ground_truth = "UNSAFE" if gt_violation else "SAFE"

        # Overhead budget
        overhead = overheads["localized"]
        target_filler = max(0, target_tokens - overhead)
        filler_res = generate_and_validate_for_tokens(target_filler, seed, encoder)
        raw_filler = filler_res["actions"]

        # Number filler sequentially
        context_obs = []
        for idx, act in enumerate(raw_filler):
            context_obs.append(action_to_observable_dict(
                label=f"F{idx+1}",
                description=act["call"],
                step=idx + 1,
                result_str=act.get("result", ""),
            ))

        # Current localized action L at step N + 1
        cur_step = len(context_obs) + 1
        current_obs = action_to_observable_dict(
            label=sec_actions[0]["label"],
            description=sec_actions[0]["description"],
            step=cur_step,
            result_str=sec_actions[0].get("result", ""),
        )

        actual_tokens = estimate_monitor_input_tokens(context_obs, current_obs, encoder, SYSTEM_PROMPT)
        evidence_step = cur_step

        return {
            "risk_structure": risk_structure,
            "sample_type": sample_type,
            "evidence_position": "current_action",
            "evidence_step": evidence_step,
            "total_steps": cur_step,
            "ground_truth": ground_truth,
            "target_tokens": target_tokens,
            "actual_tokens": actual_tokens,
            "prefix_tokens": filler_res["token_count"],
            "context_obs": context_obs,
            "current_obs": current_obs,
            "sec_actions": sec_actions,
        }

    elif risk_structure == "distributed":
        sec_actions = get_distributed_actions(sample_type)
        _st, gt_violation = execute_actions_for_ground_truth(sec_actions)
        ground_truth = "UNSAFE" if gt_violation else "SAFE"

        # Action A = classification evidence, B = job, C = destination, D = export
        act_A = sec_actions[0]
        act_B = sec_actions[1]
        act_C = sec_actions[2]
        act_D = sec_actions[3]

        # Invariance check: Action D must never repeat dataset classification
        assert "CONFIDENTIAL" not in act_D.get("result", "")
        assert "PUBLIC" not in act_D.get("result", "")
        assert "customer_records" not in act_D.get("result", "")
        assert "public_records" not in act_D.get("result", "")

        # Budget filler using canonical distributed overhead
        overhead = overheads["distributed"]
        target_filler = max(0, target_tokens - overhead)
        filler_res = generate_and_validate_for_tokens(target_filler, seed, encoder)
        raw_filler = filler_res["actions"]
        N = len(raw_filler)

        # Assemble raw sequence according to evidence_position
        # Action A is placed at beginning (index 0), middle (N // 2), or end (index N)
        # Actions B and C remain at the end, immediately preceding Action D
        if evidence_position == "beginning":
            assembled_raw = [("A", act_A)] + [("F", f) for f in raw_filler] + [("B", act_B), ("C", act_C)]
        elif evidence_position == "middle":
            mid_idx = N // 2
            assembled_raw = (
                [("F", f) for f in raw_filler[:mid_idx]]
                + [("A", act_A)]
                + [("F", f) for f in raw_filler[mid_idx:]]
                + [("B", act_B), ("C", act_C)]
            )
        elif evidence_position == "end":
            assembled_raw = [("F", f) for f in raw_filler] + [("A", act_A), ("B", act_B), ("C", act_C)]
        else:
            raise ValueError(f"Unknown evidence_position: {evidence_position}")

        # Sequentially number the history steps 1 .. len(assembled_raw)
        context_obs = []
        evidence_step = None
        for step_idx, (kind, act_data) in enumerate(assembled_raw, start=1):
            if kind == "F":
                obs = action_to_observable_dict(
                    label=f"F{step_idx}",
                    description=act_data["call"],
                    step=step_idx,
                    result_str=act_data.get("result", ""),
                )
            else:
                obs = action_to_observable_dict(
                    label=act_data["label"],
                    description=act_data["description"],
                    step=step_idx,
                    result_str=act_data.get("result", ""),
                )
                if kind == "A":
                    evidence_step = step_idx
            context_obs.append(obs)

        # Current Action D at step len(context_obs) + 1
        cur_step = len(context_obs) + 1
        current_obs = action_to_observable_dict(
            label=act_D["label"],
            description=act_D["description"],
            step=cur_step,
            result_str=act_D.get("result", ""),
        )

        actual_tokens = estimate_monitor_input_tokens(context_obs, current_obs, encoder, SYSTEM_PROMPT)

        return {
            "risk_structure": risk_structure,
            "sample_type": sample_type,
            "evidence_position": evidence_position,
            "evidence_step": evidence_step,
            "total_steps": cur_step,
            "ground_truth": ground_truth,
            "target_tokens": target_tokens,
            "actual_tokens": actual_tokens,
            "prefix_tokens": filler_res["token_count"],
            "context_obs": context_obs,
            "current_obs": current_obs,
            "sec_actions": sec_actions,
            "raw_filler_count": N,
        }
    else:
        raise ValueError(f"Unknown risk_structure: {risk_structure}")
