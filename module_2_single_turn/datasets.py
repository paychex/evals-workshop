"""Module 2 — single-turn policy Q&A dataset.

A single-turn eval tests one input -> one output. No multi-step tool dance yet;
just "ask a policy question, judge the answer." Each example carries enough
ground truth for both deterministic checks (expected_facts) and LLM judges
(reference_answer, policy_topic).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langsmith import Client

DATASET_PREFIX = os.getenv("DATASET_PREFIX", "")
DATASET_NAME = f"{DATASET_PREFIX} HR Workshop — Module 2 (single-turn Q&A)".strip()

EXAMPLES = [
    {
        "inputs": {
            "question": "How many vacation days do new full-time employees get?"
        },
        "outputs": {
            "policy_topic": "vacation",
            "expected_facts": ["15", "1.25"],
            "reference_answer": (
                "New full-time employees accrue 15 paid vacation days per year, "
                "at 1.25 days per month, usable after the 90-day probationary period."
            ),
        },
    },
    {
        "inputs": {"question": "When does my health insurance start?"},
        "outputs": {
            # Tokens kept short/robust on purpose: the agent may phrase this as
            # "the 1st of the month" or "30-day window", so we match on stable
            # substrings rather than exact wording. (A good demo of why fuzzy
            # LLM-judge correctness exists alongside brittle substring checks.)
            "policy_topic": "health_insurance",
            "expected_facts": ["first day", "30"],
            "reference_answer": (
                "Health, dental, and vision coverage begins the first day of the "
                "month following your start date. You have 30 days to enroll."
            ),
        },
    },
    {
        "inputs": {"question": "What's the 401k match and when am I eligible?"},
        "outputs": {
            "policy_topic": "401k",
            "expected_facts": ["4%", "60 days"],
            "reference_answer": (
                "The 401(k) match is 4%. You're eligible to enroll after 60 days "
                "of employment, and the match vests immediately."
            ),
        },
    },
    {
        "inputs": {"question": "Can I work from home?"},
        "outputs": {
            "policy_topic": "remote_work",
            "expected_facts": ["Tuesday", "Wednesday", "Thursday"],
            "reference_answer": (
                "We're hybrid: on-site Tuesday through Thursday, remote Monday and "
                "Friday. Fully-remote arrangements need VP approval."
            ),
        },
    },
    {
        "inputs": {
            "question": "How long do I have to submit an expense report, and do I need receipts?"
        },
        "outputs": {
            "policy_topic": "expenses",
            "expected_facts": ["30 days", "$25"],
            "reference_answer": (
                "Submit expenses within 30 days via the expense portal. Receipts "
                "are required for anything over $25."
            ),
        },
    },
]


def ensure_dataset(client: Client | None = None) -> str:
    """Create the single-turn dataset if needed; return its name (idempotent)."""
    client = client or Client()
    if client.has_dataset(dataset_name=DATASET_NAME):
        return DATASET_NAME
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="Module 2: single-turn HR policy questions with reference answers.",
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
