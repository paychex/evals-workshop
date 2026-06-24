"""Module 3 — multi-step onboarding task dataset.

Now the agent has to *do* things, not just answer. Each example is an
onboarding request whose ground truth is the expected tool-call trajectory
(plus the expected args for the key tool, and a list of tools that must NOT be
called). This is what trajectory and tool evaluators score against.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langsmith import Client

DATASET_PREFIX = os.getenv("DATASET_PREFIX", "")
DATASET_NAME = f"{DATASET_PREFIX} HR Workshop — Module 3 (agent trajectories)".strip()

# Note: lists/dicts inside example outputs are fine — LangSmith stores them as
# JSON. Evaluators read them back from reference_outputs.
EXAMPLES = [
    {
        "inputs": {
            "question": "Please get our new hire Jordan Lee set up: create their email and "
            "Slack accounts and order them a laptop."
        },
        "outputs": {
            "expected_trajectory": [
                "lookup_employee",
                "create_it_account",
                "create_it_account",
                "provision_equipment",
            ],
            "required_tools": [
                "lookup_employee",
                "create_it_account",
                "provision_equipment",
            ],
            # The agent must use Jordan's real id (E1007) once it looks them up.
            "expected_employee_id": "E1007",
            "forbidden_tools": ["schedule_orientation"],
        },
    },
    {
        "inputs": {
            "question": "Schedule orientation for Sam Rivera on their start date."
        },
        "outputs": {
            "expected_trajectory": ["lookup_employee", "schedule_orientation"],
            "required_tools": ["lookup_employee", "schedule_orientation"],
            "expected_employee_id": "E1008",
            "forbidden_tools": ["create_it_account", "provision_equipment"],
        },
    },
    {
        "inputs": {
            "question": "Alex Chen starts soon — set up their VPN access, order a laptop and a "
            "monitor, and schedule their orientation for 2026-07-01."
        },
        "outputs": {
            "expected_trajectory": [
                "lookup_employee",
                "create_it_account",
                "provision_equipment",
                "provision_equipment",
                "schedule_orientation",
            ],
            "required_tools": [
                "lookup_employee",
                "create_it_account",
                "provision_equipment",
                "schedule_orientation",
            ],
            "expected_employee_id": "E1009",
            "forbidden_tools": [],
        },
    },
    {
        "inputs": {
            "question": "What benefits plan is Jordan Lee on, and what's the 401k match for it?"
        },
        "outputs": {
            # A read-only request: look up the employee, then their plan. No
            # provisioning should happen.
            "expected_trajectory": ["lookup_employee", "get_benefits_info"],
            "required_tools": ["lookup_employee", "get_benefits_info"],
            "expected_employee_id": "E1007",
            "forbidden_tools": [
                "create_it_account",
                "provision_equipment",
                "schedule_orientation",
            ],
        },
    },
]


def ensure_dataset(client: Client | None = None) -> str:
    """Create the trajectory dataset if needed; return its name (idempotent)."""
    client = client or Client()
    if client.has_dataset(dataset_name=DATASET_NAME):
        return DATASET_NAME
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="Module 3: multi-step onboarding tasks with expected tool trajectories.",
    )
    client.create_examples(
        dataset_id=dataset.id,
        inputs=[e["inputs"] for e in EXAMPLES],
        outputs=[e["outputs"] for e in EXAMPLES],
    )
    return DATASET_NAME


if __name__ == "__main__":
    from config import require_langsmith

    require_langsmith()
    name = ensure_dataset()
    print(f"Dataset ready: {name} ({len(EXAMPLES)} examples)")
