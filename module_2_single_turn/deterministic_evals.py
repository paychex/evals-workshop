"""Module 2 — deterministic (code) evaluators for single-turn answers.

No model calls here: plain functions, fast and 100% reproducible. These cover
the objective criteria — non-empty, contains the required facts, and (the
classic "is the output the right shape?" check) structured-output validation.

Each evaluator uses the LangSmith dict signature:
    (inputs, outputs, reference_outputs) -> {"key", "score", "comment"}
You can call them directly in a unit test (see the __main__ block) or pass
them to client.evaluate.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the repo root importable when this file is run directly as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def response_not_empty(outputs: dict) -> dict:
    """The most basic guardrail: did we get a non-trivial answer at all?"""
    answer = (outputs.get("answer") or "").strip()
    ok = len(answer) >= 10
    return {
        "key": "response_not_empty",
        "score": 1 if ok else 0,
        "comment": f"Answer length = {len(answer)} chars.",
    }


def mentions_required_facts(outputs: dict, reference_outputs: dict) -> dict:
    """Did the answer include every required fact?

    Fractional score = fraction of expected facts present. This is more useful
    than pass/fail because it shows *how close* a near-miss was.
    """
    answer = (outputs.get("answer") or "").lower()
    facts = reference_outputs.get("expected_facts", [])
    if not facts:
        return {"key": "mentions_required_facts", "score": 1, "comment": "No facts required."}
    present = [f for f in facts if f.lower() in answer]
    score = len(present) / len(facts)
    missing = [f for f in facts if f not in present]
    return {
        "key": "mentions_required_facts",
        "score": score,
        "comment": f"{len(present)}/{len(facts)} facts present. Missing: {missing or 'none'}.",
    }


def no_unsupported_topic(outputs: dict, reference_outputs: dict) -> dict:
    """Cheap hallucination guard: the answer shouldn't claim a different policy topic.

    If the example is about '401k' the answer shouldn't drift into, say,
    'parental_leave'. We check that no *other* known topic keyword dominates.
    This is a heuristic — LLM groundedness (llm_judge_evals.py) is the real
    check; this just catches gross topic drift for free.
    """
    from hr_agent.knowledge import HR_POLICIES

    answer = (outputs.get("answer") or "").lower()
    target_topic = reference_outputs.get("policy_topic", "")
    other_topics = [t for t in HR_POLICIES if t != target_topic]
    # A wrong-topic keyword like "parental" or "sick" appearing is suspicious.
    leaked = [t for t in other_topics if t.replace("_", " ") in answer]
    ok = len(leaked) == 0
    return {
        "key": "no_unsupported_topic",
        "score": 1 if ok else 0,
        "comment": "No off-topic policy references." if ok else f"Mentions other topics: {leaked}.",
    }


# --- The classic "is the output the right shape?" check ------------------
# When you ask a model for *structured* output (JSON / a Pydantic object),
# the first thing to evaluate is whether the structure is valid at all. See
# structured_output.py for a target that produces this shape.

VALID_POLICY_TOPICS = {
    "vacation", "sick_leave", "remote_work", "health_insurance",
    "401k", "parental_leave", "expenses",
}


def structured_answer_is_valid(outputs: dict) -> dict:
    """Validate the SHAPE of a structured policy answer.

    Expects outputs to contain a `structured` dict with:
      - answer: non-empty string
      - policy_topic: one of the known topics
      - follow_up_needed: bool
    Returns 0 with a specific reason on the first violation.
    """
    s = outputs.get("structured")
    if not isinstance(s, dict):
        return {"key": "structured_answer_is_valid", "score": 0,
                "comment": "No 'structured' object in outputs."}

    if not isinstance(s.get("answer"), str) or not s["answer"].strip():
        return {"key": "structured_answer_is_valid", "score": 0,
                "comment": "Field 'answer' missing or empty."}

    if s.get("policy_topic") not in VALID_POLICY_TOPICS:
        return {"key": "structured_answer_is_valid", "score": 0,
                "comment": f"Invalid policy_topic: {s.get('policy_topic')!r}."}

    if not isinstance(s.get("follow_up_needed"), bool):
        return {"key": "structured_answer_is_valid", "score": 0,
                "comment": "Field 'follow_up_needed' must be a bool."}

    return {"key": "structured_answer_is_valid", "score": 1, "comment": "Valid shape."}


# Convenience bundle for the free-text experiment.
DETERMINISTIC_EVALUATORS = [
    response_not_empty,
    mentions_required_facts,
    no_unsupported_topic,
]


if __name__ == "__main__":
    # Unit-test the evaluators on known good/bad outputs — no API needed.
    # This is a habit worth teaching: validate your evaluator before trusting it.
    good = {"answer": "New hires accrue 15 days, at 1.25 days per month."}
    ref = {"expected_facts": ["15", "1.25"], "policy_topic": "vacation"}
    assert mentions_required_facts(good, ref)["score"] == 1.0
    assert mentions_required_facts({"answer": "about 15 days"}, ref)["score"] == 0.5
    assert response_not_empty({"answer": ""})["score"] == 0

    assert structured_answer_is_valid(
        {"structured": {"answer": "15 days", "policy_topic": "vacation", "follow_up_needed": False}}
    )["score"] == 1
    assert structured_answer_is_valid({"structured": {"answer": "", "policy_topic": "vacation",
                                                       "follow_up_needed": False}})["score"] == 0
    assert structured_answer_is_valid({"structured": {"answer": "x", "policy_topic": "nope",
                                                       "follow_up_needed": False}})["score"] == 0
    print("All deterministic evaluator self-tests passed.")
