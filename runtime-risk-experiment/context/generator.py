"""
context/generator.py

Benign filler context generation and token accounting using tiktoken.
"""

import random
from typing import List, Dict, Any
import tiktoken


def get_encoder(name: str = "cl100k_base"):
    """Return tiktoken encoder."""
    return tiktoken.get_encoding(name)


BENIGN_TEMPLATES = [
    ('run_data_quality_check(dataset="analytics_logs_{id}")', 'Quality check complete. 0 warnings found.'),
    ('read_file_metadata(file_id="system_metrics_{id}")', 'Metadata retrieved. Size: {size}KB. Status: OK.'),
    ('compute_statistics(dataset="audit_events_{id}", metrics="mean,std")', 'Statistics computed. Records processed: {records}.'),
    ('validate_schema(dataset="telemetry_{id}")', 'Schema valid. 18 fields verified.'),
    ('check_disk_usage(volume="vol_{id}")', 'Disk usage: {pct}% utilized.'),
    ('archive_logs(service="svc_{id}", retention_days=30)', 'Log archive job scheduled.'),
    ('sync_cache(region="us-east-{id}")', 'Cache synchronized successfully.'),
    ('format_report(report_id="rep_{id}", format="csv")', 'Report formatted. Output: report_{id}.csv.'),
]


def action_to_observable_dict(label: str, description: str, step: int, result_str: str = "") -> Dict[str, Any]:
    """Convert an action to an observable record dict."""
    return {
        "label": label,
        "step": step,
        "call": description,
        "result": result_str,
    }


def actions_to_text(actions: List[Dict[str, Any]]) -> str:
    """Format observable action dicts into readable text."""
    lines = []
    for a in actions:
        step = a.get("step")
        call = a.get("call") or a.get("description", "")
        result = a.get("result", "")
        if step is not None:
            if result:
                lines.append(f"Step {step}: {call} -> {result}")
            else:
                lines.append(f"Step {step}: {call}")
        else:
            if result:
                lines.append(f"{call} -> {result}")
            else:
                lines.append(f"{call}")
    return "\n".join(lines)


def generate_and_validate_for_tokens(target_tokens: int, seed: int, encoder=None) -> Dict[str, Any]:
    """
    Generate benign filler actions to reach approximately target_tokens.
    Deterministic with respect to seed.
    """
    if encoder is None:
        encoder = get_encoder()

    if target_tokens <= 0:
        return {"actions": [], "token_count": 0}

    rng = random.Random(seed)
    actions = []
    current_tokens = 0
    step = 1

    while current_tokens < target_tokens:
        tmpl, res_tmpl = rng.choice(BENIGN_TEMPLATES)
        item_id = rng.randint(100, 999)
        call_str = tmpl.format(id=item_id)
        res_str = res_tmpl.format(id=item_id, size=rng.randint(10, 500), records=rng.randint(100, 5000), pct=rng.randint(20, 85))
        
        obs = action_to_observable_dict(f"F{step}", call_str, step=step, result_str=res_str)
        text = actions_to_text([obs])
        token_cost = len(encoder.encode(text + "\n"))
        
        # If adding this would significantly overshoot when close, break
        if actions and (current_tokens + token_cost > target_tokens + 20):
            break

        actions.append(obs)
        current_tokens += token_cost
        step += 1

    full_text = actions_to_text(actions)
    actual_tokens = len(encoder.encode(full_text)) if full_text else 0

    return {
        "actions": actions,
        "token_count": actual_tokens,
        "text": full_text,
    }
