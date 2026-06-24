# Module 2 — Single-Turn Evaluations

> Goal: evaluate one input → one output. Master the two evaluator families —
> deterministic code checks and LLM-as-judge — on the HR agent's policy answers.

A *single-turn* eval ignores how the agent got there; it judges the final
answer to a single question. It's the right starting point because the
techniques here (exact/fuzzy matching, shape validation, reference grading,
groundedness) are the building blocks you'll reuse in the harder agent evals.

## What's here

| File | What it teaches |
|------|-----------------|
| `datasets.py` | A 5-example policy Q&A dataset with rich ground truth (`expected_facts`, `reference_answer`, `policy_topic`). |
| `deterministic_evals.py` | Code evaluators: non-empty, required-facts (fractional), topic-drift guard, and **structured-output shape validation**. |
| `llm_judge_evals.py` | LLM-as-judge evaluators with structured output: correctness, groundedness (anti-hallucination), professional tone. |
| `structured_output.py` | A target that returns a typed object + the "is the output the right shape?" check. |
| `run_eval.py` | The full experiment: deterministic + LLM judges together. |

## Run it

```bash
# Unit-test the deterministic evaluators first — no API key needed.
uv run python module_2_single_turn/deterministic_evals.py

# The full single-turn experiment (deterministic + LLM judges).
uv run python module_2_single_turn/run_eval.py

# The structured-output shape-validation experiment.
uv run python module_2_single_turn/structured_output.py
```

## Key ideas to land

1. **Deterministic first.** `mentions_required_facts` and
   `structured_answer_is_valid` cost nothing and never flake. Most "is it
   broken?" questions are objective — answer them with code.
2. **Fractional scores beat pass/fail** for partial credit (`2/3 facts
   present` is more actionable than a bare `0`).
3. **LLM judges need structure.** We return a Pydantic object
   (`reasoning` + verdict), never free text. The `reasoning` becomes the
   evaluator comment so a surprising score is always explainable.
4. **Groundedness ≠ correctness.** An answer can match the reference yet add a
   hallucinated detail. We grade them separately, feeding the judge the *real*
   policy text as the source of truth.
5. **Validate your evaluators.** `deterministic_evals.py` has self-tests on
   known good/bad outputs. An untrusted evaluator is worse than none.

> Production tip: LangChain's [`openevals`](https://github.com/langchain-ai/openevals)
> ships ready-made correctness/groundedness judges. We build them by hand here
> so the mechanics are clear — reach for `openevals` once they are.

Next: **Module 3**, where we stop judging the final answer alone and start
judging *how the agent got there* — the tool-call trajectory.
