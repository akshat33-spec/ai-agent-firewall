"""
experiments/run_calibration.py

Orchestrates calibration sweeps across token context targets.
"""

from typing import List, Dict, Any
from detector.monitor import SYSTEM_PROMPT, build_user_prompt
from context.generator import get_encoder


def estimate_monitor_input_tokens(
    context_actions: List[Dict[str, Any]],
    current_action: Dict[str, Any],
    encoder=None,
    system_prompt: str = SYSTEM_PROMPT,
) -> int:
    """
    Measure total monitor input tokens (system prompt + user prompt) using tiktoken.
    """
    if encoder is None:
        encoder = get_encoder()

    user_prompt = build_user_prompt(context_actions, current_action)
    total_text = f"{system_prompt}\n{user_prompt}"
    return len(encoder.encode(total_text))
