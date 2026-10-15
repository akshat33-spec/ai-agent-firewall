"""
environment/state.py

Represents the deterministic environment state for Scenario 1 (Unauthorized External Data Export).
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class EnvironmentState:
    selected_dataset: Optional[str] = None
    dataset_classification: Optional[str] = None
    export_job_created: bool = False
    destination_configured: Optional[str] = None
    export_executed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


def initial_state() -> EnvironmentState:
    """Return a fresh initial environment state."""
    return EnvironmentState()
