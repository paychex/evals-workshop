"""Module 2 — LLM-as-judge evaluators for single-turn answers.

Use a model to grade the fuzzy qualities deterministic code can't: is the
answer *correct* (same meaning as the reference), is it *grounded* in real
policy (not hallucinated), and is the *tone* appropriate for a new hire?

Best practices baked in here:
  - Structured output (Pydantic) so we get a reliable score + reasoning,
    never free text we have to parse.
  - Temperature 0 judge for stability.
  - The reasoning is returned as the evaluator `comment`, so when a score
    looks wrong you can read *why* the judge decided it in the LangSmith UI.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from config import get_judge


class CorrectnessGrade(BaseModel):
    reasoning: str = Field(description="One or two sentences explaining the judgment.")
    is_correct: bool = Field(description="True if the answer matches the reference in meaning.")


class GroundednessGrade(BaseModel):
    reasoning: str = Field(description="Explain whether every claim is supported.")
    is_grounded: bool = Field(description="True if all claims are supported by the policy text.")


class ToneGrade(BaseModel):
    reasoning: str = Field(description="Explain the tone judgment.")
    score: int = Field(description="1=poor, 2=acceptable, 3=excellent (warm, clear, professional).", ge=1, le=3)


def correctness(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """LLM judge: does the answer match the reference answer in meaning?"""
    judge = get_judge().with_structured_output(CorrectnessGrade)
    prompt = f"""You are grading an HR assistant's answer for factual correctness.

Question: {inputs.get('question', '')}
Reference answer (ground truth): {reference_outputs.get('reference_answer', '')}
Assistant answer: {outputs.get('answer', '')}

Is the assistant's answer correct — does it convey the same key facts as the
reference? Minor wording differences are fine; wrong or missing numbers are not."""
    grade = judge.invoke(prompt)
    return {
        "key": "correctness",
        "score": 1 if grade.is_correct else 0,
        "comment": grade.reasoning,
    }


def groundedness(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """LLM judge: is every claim supported by the official policy text?

    This is the anti-hallucination metric. We feed the judge the *actual*
    policy from the knowledge base as the source of truth.
    """
    from hr_agent.knowledge import HR_POLICIES

    topic = reference_outputs.get("policy_topic", "")
    source = HR_POLICIES.get(topic, "(no policy text available)")
    judge = get_judge().with_structured_output(GroundednessGrade)
    prompt = f"""You are checking an HR assistant's answer for hallucination.

Official policy (the ONLY source of truth):
\"\"\"{source}\"\"\"

Assistant answer: {outputs.get('answer', '')}

Is every factual claim in the answer supported by the official policy above?
If the answer adds numbers, dates, or rules not present in the policy, it is
NOT grounded."""
    grade = judge.invoke(prompt)
    return {
        "key": "groundedness",
        "score": 1 if grade.is_grounded else 0,
        "comment": grade.reasoning,
    }


def professional_tone(inputs: dict, outputs: dict) -> dict:
    """LLM judge: is the tone warm, clear, and professional for a new hire?"""
    judge = get_judge().with_structured_output(ToneGrade)
    prompt = f"""Rate the tone of this HR assistant reply to a new employee.

Reply: {outputs.get('answer', '')}

Score 1 (poor: cold, confusing, or unprofessional), 2 (acceptable), or
3 (excellent: warm, clear, concise, professional)."""
    grade = judge.invoke(prompt)
    # Normalize 1-3 to 0-1 so it sits on the same scale as the other metrics.
    return {
        "key": "professional_tone",
        "score": (grade.score - 1) / 2,
        "comment": f"Raw {grade.score}/3. {grade.reasoning}",
    }


LLM_JUDGE_EVALUATORS = [correctness, groundedness, professional_tone]
