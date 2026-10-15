"""
verify_v11.py
Pre-calibration verification:
  1. Confirm PROMPT_VERSION == v1.1 in detector
  2. Confirm calibration_config.json has prompt_version == v1.1
  3. Show the exact current-action text for all 4 trajectory types
     so the researcher can confirm classification metadata is present
     in what the monitor will actually see.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from detector.monitor import PROMPT_VERSION, SYSTEM_PROMPT
from experiments.run_experiment import (
    get_localized_actions,
    get_distributed_actions,
    build_monitor_input,
)
from context.generator import get_encoder, generate_and_validate_for_tokens, actions_to_text

OK = True

# ---- 1. Prompt version ----
print("[ 1 ] Prompt version in detector/monitor.py")
if PROMPT_VERSION == "v1.1":
    print(f"  [OK] PROMPT_VERSION = {PROMPT_VERSION!r}")
else:
    print(f"  [FAIL] PROMPT_VERSION = {PROMPT_VERSION!r}  (expected 'v1.1')")
    OK = False

# ---- 2. Config file ----
print("\n[ 2 ] calibration_config.json")
with open("calibration_config.json") as f:
    cfg = json.load(f)
pv = cfg.get("prompt_version", "MISSING")
if pv == "v1.1":
    print(f"  [OK] prompt_version = {pv!r}")
else:
    print(f"  [FAIL] prompt_version = {pv!r}  (expected 'v1.1')")
    OK = False
print(f"  seeds           = {cfg.get('seeds')}")
print(f"  token_levels    = {cfg.get('calibration_token_levels')}")
print(f"  risk_structures = {cfg.get('risk_structures')}")
print(f"  sample_types    = {cfg.get('sample_types')}")
total = (len(cfg.get('calibration_token_levels', [])) *
         len(cfg.get('risk_structures', [])) *
         len(cfg.get('seeds', [])) *
         len(cfg.get('sample_types', [])))
print(f"  Total trials    = {total}  (expected 280)")
if total != 280:
    print(f"  [FAIL] Trial count mismatch!")
    OK = False

# ---- 3. Observable action text for all 4 trajectory types ----
print("\n[ 3 ] Observable action text passed to monitor")
encoder = get_encoder("cl100k_base")

CASES = [
    ("localized",   "positive"),
    ("localized",   "negative"),
    ("distributed", "positive"),
    ("distributed", "negative"),
]

for structure, sample_type in CASES:
    if structure == "localized":
        actions = get_localized_actions(sample_type)
        decision_idx = 0
    else:
        actions = get_distributed_actions(sample_type)
        decision_idx = len(actions) - 1

    _, current_obs = build_monitor_input([], actions, decision_idx)
    current_text = actions_to_text([current_obs])

    # Check classification keyword is present
    if structure == "localized":
        expected_kw = "CONFIDENTIAL" if sample_type == "positive" else "PUBLIC"
    else:
        # For distributed, classification appears in action A (in history, not current)
        # Current action is D (execute_export) — no classification there
        # Check history action A
        history_obs, _ = build_monitor_input([], actions, decision_idx)
        # history_obs is empty (no filler), so check action A manually
        from experiments.run_experiment import action_to_observable_dict
        a_obs = action_to_observable_dict(actions[0]["label"], actions[0]["description"],
                                          step=1, result_str=actions[0].get("result",""))
        history_text = actions_to_text([a_obs])
        expected_kw = "CONFIDENTIAL" if sample_type == "positive" else "PUBLIC"
        kw_present = expected_kw in history_text
        print(f"  [{structure:12s} / {sample_type:8s}]")
        print(f"    Action A observable: {history_text.strip()}")
        print(f"    Classification keyword '{expected_kw}' in Action A: {'[OK]' if kw_present else '[FAIL]'}")
        if not kw_present:
            OK = False
        print(f"    Current action (D):  {current_text.strip()}")
        continue

    kw_present = expected_kw in current_text
    print(f"  [{structure:12s} / {sample_type:8s}]")
    print(f"    Current action: {current_text.strip()}")
    print(f"    Classification keyword '{expected_kw}' present: {'[OK]' if kw_present else '[FAIL]'}")
    if not kw_present:
        OK = False

# ---- 4. System prompt policy lines ----
print("\n[ 4 ] System prompt policy content")
checks = [
    "CONFIDENTIAL",
    "PUBLIC",
    "external_storage",
    "not confidential",
]
for kw in checks:
    if kw in SYSTEM_PROMPT:
        print(f"  [OK] '{kw}' present in SYSTEM_PROMPT")
    else:
        print(f"  [FAIL] '{kw}' MISSING from SYSTEM_PROMPT")
        OK = False

print("\n" + "=" * 60)
print("PRE-CALIBRATION CHECK:", "PASSED — safe to run calibration" if OK else "FAILED — do not run calibration")
print("=" * 60)
