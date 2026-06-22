"""Module 3 — LLM-as-judge over the trajectory.

Deterministic trajectory checks need an expected path written in advance.
Sometimes there's no single right path, or you want a holistic "was this a
sensible way to handle the request?" verdict. That's where an LLM judge over
the trajectory earns its keep.

We hand the judge the user's request and the actual sequence of tool calls
(with args) and ask whether the agent's plan was reasonable, complete, and
free of unnecessary or risky steps.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from config import get_judge


class TrajectoryGrade(BaseModel):
    reasoning: str = Field(description="Explain the judgment in 1-3 sentences.")
    is_reasonable: bool = Field(
        description="True if the tool sequence was a sensible, complete way to fulfill the request."
    )


def _format_calls(tool_calls: list[dict]) -> str:
    if not tool_calls:
        return "(the agent made no tool calls)"
    return "\n".join(
        f"{i+1}. {c['name']}({c.get('args', {})})" for i, c in enumerate(tool_calls)
    )


def trajectory_is_reasonable(inputs: dict, outputs: dict) -> dict:
    """LLM judge: was the agent's tool-call plan sensible and complete?"""
    judge = get_judge().with_structured_output(TrajectoryGrade)
    prompt = f"""You are reviewing an HR onboarding agent's actions.

User request:
{inputs.get('question', '')}

The agent made these tool calls, in order:
{_format_calls(outputs.get('tool_calls', []))}

Available tools: lookup_employee, lookup_hr_policy, get_benefits_info,
create_it_account, provision_equipment, schedule_orientation.

Was this a reasonable and complete way to handle the request? It is NOT
reasonable if the agent skipped a required action, performed an action the
user did not ask for, looked up the wrong person, or took clearly redundant
steps."""
    grade = judge.invoke(prompt)
    return {
        "key": "trajectory_is_reasonable",
        "score": 1 if grade.is_reasonable else 0,
        "comment": grade.reasoning,
    }


LLM_TRAJECTORY_EVALUATORS = [trajectory_is_reasonable]
