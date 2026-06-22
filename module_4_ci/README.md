# Module 4 — Evaluations in CI

> Goal: turn the evals from Modules 2 & 3 into an automated gate that fails the
> build when quality regresses — so prompt/model/tool changes are caught in the
> PR, not in production.

## Two gating patterns (use both)

| Pattern | File | What it gives you | Best for |
|---------|------|-------------------|----------|
| **Per-example gate** | `test_evals.py` | One pytest case per dataset example. CI shows *exactly which* example broke. | Deterministic, safety-critical checks you want to hard-block on. |
| **Aggregate gate** | `ci_gate.py` | Mean score per metric vs a threshold; non-zero exit fails the build. | Dataset-level quality bars, including fuzzy LLM-judge metrics tracked as trends. |

A good rule: **hard-assert the deterministic/safety metrics per-example**
(never call a forbidden tool, always use the right employee id), and **gate the
fuzzy quality metrics in aggregate** (correctness ≥ 0.8 across the set), since
a single LLM-judge call can be noisy but the mean is stable.

## Run locally

```bash
# Per-example tests
pytest module_4_ci/test_evals.py -v --langsmith-output

# Aggregate gates (exit non-zero on regression)
python module_4_ci/ci_gate.py --suite single_turn
python module_4_ci/ci_gate.py --suite agent
```

## The GitHub Actions workflow

[`.github/workflows/evals.yml`](../.github/workflows/evals.yml) runs all three
on every PR. Add `LANGSMITH_API_KEY` and `ANTHROPIC_API_KEY` under **repo
Settings → Secrets and variables → Actions**. Experiments are tagged with the
commit SHA so a regression traces straight back to the PR that caused it.

## Setting thresholds (the hard part)

Thresholds live in `THRESHOLDS` in `ci_gate.py`. Guidance:

- **Safety/format metrics → 1.0.** `no_forbidden_tools`, `correct_employee_id`,
  `tool_args_well_formed`, `response_not_empty` should never regress.
- **Quality metrics → a touch below current baseline.** Run the suite a few
  times on `main`, take the stable mean, set the threshold slightly under it.
  Too tight and flaky judges block good PRs; too loose and real regressions slip
  through.
- **Trajectory exact-match → keep low (or off as a gate).** It's a useful
  *signal* but too brittle to block merges on; prefer `required_tools_used`.
- **Watch cost & time.** Evals call models. Keep the CI dataset small and
  curated (10–50 sharp examples), and run the big nightly suite on a schedule,
  not on every PR.

## Common patterns beyond this repo

- **Regression vs. baseline**, not absolute threshold: compare this PR's
  experiment to `main`'s and fail only on a *drop* (LangSmith stores both).
- **Sampling on every PR, full suite nightly** (a scheduled workflow) to balance
  signal against cost.
- **Block on safety, report on quality**: hard-fail safety metrics; post quality
  deltas as a PR comment for human review rather than auto-blocking.

---

## 🗣️ Live discussion (facilitator-led — not in code)

> These are conversation prompts for the session, intentionally left for the
> presenter rather than fabricated here:
>
> - **How we run evals in CI internally** — Eric to walk through the real
>   pipeline: what gates on PR vs. nightly, how thresholds/baselines are set,
>   how flaky-judge noise is handled, and cost controls.
> - **Partner success stories** — examples from other teams: what they gated
>   on, what regressions evals caught before release, and lessons learned.
> - **Open Q&A** — map these patterns onto *your* services and existing CI.
