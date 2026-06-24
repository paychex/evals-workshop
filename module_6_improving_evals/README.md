# Module 6 — Improving Evals (Annotation & Few-Shot)

> Goal: when your LLM judge disagrees with your humans, fix it — without
> fine-tuning. Capture human judgment with an **annotation queue**, then **align**
> the judge with a handful of those labels as few-shot examples.

An LLM judge is only useful if its scores track what your team actually considers
good. Out of the box they often don't: a generic judge grades against a generic
notion of quality and misses your house style, your edge cases, your bar. A judge
you can't trust is worse than no judge — it gives wrong answers *confidently*.

The loop that fixes this:

```
   production traces
        │  queue the ones worth a look
        ▼
   annotation queue  ──►  human labels (ground truth)
        │                      │
        │                      ├──►  measure judge agreement ("evaluate the evaluator")
        │                      └──►  feed back as few-shot examples ──►  aligned judge
        ▼
   curate the best into your offline dataset (the flywheel from Module 5)
```

## What's here

| File | What it teaches |
|------|-----------------|
| `annotation_queue.py` | Create a queue and push the **flagged** production traces to it for human review. (Picks the traces your online evals scored low — `score_traces.py`'s feedback — falling back to the deterministic checks.) |
| `few_shot_judge.py` | One judge ("does this meet our HR house style?") that runs zero-shot (rubric only) or few-shot (rubric + human-labeled examples). |
| `judge_alignment.py` | **Evaluate the evaluator**: measure how often the judge agrees with humans, zero-shot vs few-shot, on a held-out label set. |

## Run it

```bash
# Measure judge↔human agreement, zero-shot vs few-shot (needs a model key).
uv run python module_6_improving_evals/judge_alignment.py

# Push flagged production traces to an annotation queue for labeling.
# (Run module_5_online_evals/production_traffic.py first to create traces.)
uv run python module_6_improving_evals/annotation_queue.py
#   --all     queue recent traces, not just the flagged ones
```

`judge_alignment.py` prints the zero-shot agreement, the few-shot agreement, and
the lift. The few-shot examples it uses are a held-out slice of the same human
labels — exactly what you'd harvest from the annotation queue.

## Key ideas to land

1. **Evaluate the evaluator.** Before trusting an LLM judge, measure its agreement
   with human labels. Agreement *is* the judge's accuracy.
2. **Annotation queues are how human judgment scales.** Queue the traces worth a
   human's time (the flagged ones), label them once, reuse the labels everywhere.
3. **Few-shot beats prompt-wrangling for alignment.** Showing the judge real
   labeled examples moves it toward your reviewers faster than rewriting the
   rubric — and needs no fine-tuning.
4. **Never score the judge on its own few-shot examples.** Hold out a separate
   slice, or you're measuring memorization, not alignment.
5. **Labels are reusable.** The same human labels measure the judge, align the
   judge, and seed the offline dataset.

## How this connects to LangSmith

- **Annotation Queues** (UI: *Annotation Queues*) are first-class. You can attach a
  **rubric** to a queue so reviewers grade against consistent criteria; their
  feedback lands on the runs as scores you can query with `client.list_feedback`.
- **Corrections → few-shot, automatically.** When a reviewer corrects a run in a
  LangSmith dataset, those corrections can be served back as few-shot examples to
  the judge — the productized version of what `few_shot_judge.py` does by hand.
- We build the alignment loop by hand here so the mechanics are clear. In practice,
  pair queues + datasets + [`openevals`](https://github.com/langchain-ai/openevals)
  judges, which already accept few-shot examples.

Next: **Module 7** — run the reference-free evals from Module 5 on a schedule as a
production monitor that alerts when quality drifts.
