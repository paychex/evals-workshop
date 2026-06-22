# Facilitator Guide — Evaluations Workshop

How to run and narrate the full workshop. It's two ~half-day sessions built on one
example app (the HR Onboarding agent in `hr_agent/`):

- **Session 1 — Foundations (Modules 1–4):** what an eval is, single-turn and
  agent evals, and gating a PR with an offline suite.
- **Session 2 — Evals for Production (Modules 5–7):** online evals on live traces,
  improving evaluators with annotation + few-shot, and monitoring for drift.

Each module is a 30–60 min block: a short talk, a live demo, then attendees run it
themselves. You can teach the sessions on separate days or back-to-back as a full
day.

## Before you start

1. **Keys set** in `.env`: `LANGSMITH_API_KEY` + `ANTHROPIC_API_KEY` (see
   `.env.example`). Confirm with self-tests that need no network:
   ```bash
   python module_2_single_turn/deterministic_evals.py
   python module_3_agent_evals/trajectory_evals.py
   python module_5_online_evals/reference_free_evals.py
   ```
2. **Before Session 2, reset the demo state** so the live run looks fresh (deletes
   the `hr-agent-production` project and the annotation queue):
   ```bash
   python reset_demo.py
   ```
3. Have **smith.langchain.com** open on the projector — most of the payoff is
   visual (per-example scores, judge reasoning in comments, the annotation queue,
   the monitor output).

## The whole-workshop through-line (open Session 1 with this)

> "You can't improve what you can't measure. An eval is just a *repeatable,
> automated answer to 'is the agent doing the right thing?'* We'll start with the
> four parts every eval shares, build up to judging an agent's whole trajectory,
> gate a build on it — and then take it to production: scoring live traffic,
> aligning our judges to human taste, and alerting on drift."

The same HR agent is the system-under-test the entire way through — they learn the
app once, then everything else is *evaluation technique*.

---

# SESSION 1 — Foundations

## Module 1 — Fundamentals (~30 min)

**Talk track:** "Every evaluation — single-turn or agentic, code or LLM-judged — is
four moving parts: a **Dataset** (examples with inputs and maybe ground truth), a
**Target** (the thing under test — our agent), an **Evaluator** (scores one
example), and an **Experiment** (one run of the target over the dataset, tracked in
LangSmith). And there are two families of evaluator: **deterministic** code checks
and **LLM-as-judge**. Rule of thumb: reach for deterministic first; only use a
judge for things code genuinely can't capture."

**Demo:**
```bash
python module_1_fundamentals/01_first_eval.py     # 3 examples, the agent, one deterministic check
```
**The moment to land:** open the experiment in LangSmith and show the per-example
score grid. "This view — inputs, outputs, a score column per evaluator — is where
you'll live for the rest of the workshop."

## Module 2 — Single-Turn Evals (~60 min)

**Talk track:** "Single-turn judges the final answer to one question and ignores
how the agent got there. Deterministic first: is it non-empty, does it contain the
required facts, is the structured output the right shape? Then LLM judges for the
fuzzy stuff — correctness against a reference, **groundedness** (anti-hallucination),
tone. Two rules: judges return *structured output with reasoning* (never free text
you have to parse), and the reasoning becomes the evaluator comment, so a
surprising score is always explainable."

**Demo, in order:**
```bash
python module_2_single_turn/deterministic_evals.py   # self-test, no keys — validate the evaluator first
python module_2_single_turn/run_eval.py              # deterministic + LLM judges together
python module_2_single_turn/structured_output.py     # the "is it the right shape?" check
```
**The moment to land:** in LangSmith, sort by `groundedness`, open a low one, and
read the judge's reasoning in the comment. "Groundedness ≠ correctness — an answer
can match the reference *and* add a hallucinated detail. We grade them separately,
feeding the judge the real policy text as the source of truth."

## Module 3 — Agent Evals (Trajectory & Tools) (~60 min)

**Talk track:** "A correct-sounding final message can hide a broken *process*: the
agent called a destructive tool it shouldn't have, looked up the wrong employee, or
took ten steps for a two-step job. Agent evals judge the **trajectory** and the
**tool arguments**, not just the answer. Three lenses: path (right tools, sane
order, nothing forbidden), arguments (right employee_id, valid enums), and judgment
(an LLM judge for open-ended tasks with no single right path)."

**Demo:**
```bash
python module_3_agent_evals/trajectory_evals.py      # self-test, no keys
python module_3_agent_evals/tool_evals.py            # self-test, no keys
python module_3_agent_evals/run_eval.py              # one agent run feeds all three lenses
```
**The moment to land:** the **forbidden-tool** safety check. "'Did NOT provision
equipment on a read-only benefits question' is often more important than 'did Y'.
And notice exact-match is brittle — we layer `required_tools_used` (order-agnostic)
and `efficiency` so a non-exact run tells you *how* it differed instead of a flat
fail."

## Module 4 — Evals in CI (~45 min)

**Talk track:** "Now turn those experiments into a gate that fails the build when
quality regresses — so a bad prompt/model/tool change is caught in the PR, not in
production. Two patterns, use both: a **per-example gate** (pytest — CI shows
exactly which example broke; hard-block your safety checks) and an **aggregate
gate** (mean score vs a threshold — best for fuzzy judge metrics, where one call is
noisy but the mean is stable). The rule: hard-assert safety per-example, gate fuzzy
quality in aggregate."

**Demo:**
```bash
pytest module_4_ci/test_evals.py -v --langsmith-output   # per-example gate
python module_4_ci/ci_gate.py --suite single_turn        # aggregate gate
python module_4_ci/ci_gate.py --suite agent
```

**The killer beat — make the gate go red live.** Demonstrate a real regression:
1. In `hr_agent/agent.py`, comment out the system-prompt line *"For policy
   questions, ALWAYS call lookup_hr_policy and ground your answer…"*.
2. Re-run `python module_4_ci/ci_gate.py --suite single_turn` → **groundedness
   drops below threshold, gate exits non-zero, build fails.**
3. Restore the line, re-run → green again.

> "That's the whole point: the gate caught a quality regression a unit test never
> would have."

Then show [`.github/workflows/evals.yml`](.github/workflows/evals.yml) — runs all
three on every PR, experiments tagged with the commit SHA.

🗣️ **Live discussion** (Module 4 README has prompts): how we run evals in CI
internally — what gates on PR vs nightly, how thresholds/baselines are set, how
flaky-judge noise is handled — plus partner success stories.

**Bridge to Session 2:** "This protects your *pull request*. But your curated
dataset can't anticipate what real users actually ask. Session 2 takes evals to
production."

---

# SESSION 2 — Evals for Production

Open by drawing the flywheel and keep pointing back at it:

```
offline dataset ──ship──► production traces ──online evals──► flagged traces
      ▲                                                            │
      └──────── curate ◄──── human annotation ◄────────────────────┘
                              │
                              └──► few-shot ──► aligned judges
```

> "Session 1 got evals into your *pull request*. Session 2 gets them into
> *production*. It's one loop: the offline dataset can't anticipate what real users
> ask → online evals catch what it missed → humans label the interesting failures →
> those labels align your judges *and* feed back into the dataset. By the end you'll
> have a monitor that pages you when production quality drifts."

## Module 5 — Experiments vs. Tracing (~45 min)

**Talk track:** "Everything in Session 1 had a `reference_outputs` — ground truth.
A live production trace has none. That single constraint *defines* online evals:
you can only use what's in the trace, plus knowledge you already hold."

**Demo, in order:**
```bash
python module_5_online_evals/reference_free_evals.py   # self-test, no keys — show the (inputs, outputs) signature
python module_5_online_evals/production_traffic.py     # 10 messy real-user queries → traced
python module_5_online_evals/score_traces.py           # pull traces → score → write feedback
```

**The moment to land:** open the `hr-agent-production` project in LangSmith and
sort by `groundedness`. It sits around **0.70** — and the misses are the vague
"what's the deal with benefits?" answers that cite benefits-plan data *outside* the
policy corpus.

> "Nobody wrote a test for that question. Online evals found a real gap a curated
> dataset never would. That trace is now the single most valuable thing to add
> *back* to the offline set." ← that's the flywheel, made concrete.

Then point at the README's **server-side rules** section: "In production you don't
run this loop from your laptop — you attach the evaluator as a *rule* that
auto-scores ~10% of traffic. Same evaluator, no job to babysit."

## Module 6 — Improving Evals (~60 min)

**Talk track:** "An LLM judge is only worth something if its scores track *your*
humans. Out of the box they often don't. So first you *evaluate the evaluator*,
then you fix it — no fine-tuning."

**Demo:**
```bash
python module_6_improving_evals/judge_alignment.py     # zero-shot vs few-shot agreement
```

**The reveal:** zero-shot agrees with humans ~**75%**, few-shot ~**100%** — a clear
lift. Then explain *why*: the rubric is deliberately vague; the team's real
convention ("every reply must end with an invitation to follow up") lives *only* in
the labeled examples.

> "This is every team style that's in your reviewers' heads but not in a doc. The
> model can't guess it — but four labeled examples teach it."

(Judges are noisy; the exact numbers vary run to run. If you get no lift, run it
again or add examples — the script says as much. The *method* is the lesson.)

```bash
python module_6_improving_evals/annotation_queue.py    # queues the traces the online evals flagged
```

> "Where do those labels come from? You don't label everything — you label what the
> online evals flagged. Queue it, a human renders a verdict, and that verdict does
> triple duty: it measures the judge, aligns the judge, and seeds the dataset."

Open the annotation queue in LangSmith and label one trace live so they see the
reviewer experience.

## Module 7 — Production CI (~45 min)

**Talk track:** "Module 4 gated a *merge*. But plenty of regressions never appear in
a diff — a provider updates the model behind your API, a data source goes stale.
Your offline suite is green and production is rotting. You need a second gate, on
production behavior *over time*."

**Demo:**
```bash
python module_7_production_ci/monitor.py               # mean per metric vs baseline.json → exit 0 / alert
```

**The teaching beat — lean into the noise.** The groundedness judge wobbles
run-to-run on a small sample (≈0.70↔0.90). Use it live:

> "This is exactly why we gate on **drift vs. a baseline within a tolerance**, not
> an absolute threshold — and why you average over many traces. One noisy judge
> call means nothing; the mean is stable."

To force a `DRIFT` alert on demand (great for showing the gate bite): tighten the
tolerance or lower the baseline.
```bash
# Edit module_7_production_ci/baseline.json: set "tolerance": 0.01, then:
python module_7_production_ci/monitor.py               # now exits non-zero
```

Then show [`.github/workflows/online-evals.yml`](.github/workflows/online-evals.yml):
the nightly `cron`, and the commented `if: failure()` Slack step. "Non-zero exit
fails the scheduled job — that's your page."

## Close (~15 min) — map it to their world

- What's your production project today?
- What's one **reference-free** check you could run on it tomorrow?
- What convention is in your reviewers' heads that a judge can't currently guess —
  and could you give it three labeled examples?

🗣️ Optional live discussion: how we run online evals + alerting in our own stack,
and sampling/cost trade-offs at high traffic.

---

## Quick reference

**Session 1 — Foundations**

| Step | Command |
|------|---------|
| First eval | `python module_1_fundamentals/01_first_eval.py` |
| Single-turn experiment | `python module_2_single_turn/run_eval.py` |
| Structured-output check | `python module_2_single_turn/structured_output.py` |
| Agent (trajectory/tools) experiment | `python module_3_agent_evals/run_eval.py` |
| Per-example CI gate | `pytest module_4_ci/test_evals.py -v --langsmith-output` |
| Aggregate CI gate | `python module_4_ci/ci_gate.py --suite single_turn` (or `--suite agent`) |

**Session 2 — Evals for Production**

| Step | Command |
|------|---------|
| Reset demo state | `python reset_demo.py` |
| Generate traffic | `python module_5_online_evals/production_traffic.py` |
| Online-eval loop | `python module_5_online_evals/score_traces.py` |
| Judge alignment | `python module_6_improving_evals/judge_alignment.py` |
| Annotation queue | `python module_6_improving_evals/annotation_queue.py` |
| Production monitor | `python module_7_production_ci/monitor.py` |
| Recapture baseline | `python module_7_production_ci/monitor.py --write-baseline --limit 200` |

**Self-tests (no keys, no network)** — good warm-ups before each session:
```bash
python module_2_single_turn/deterministic_evals.py
python module_3_agent_evals/trajectory_evals.py
python module_3_agent_evals/tool_evals.py
python module_5_online_evals/reference_free_evals.py
```

Cost note: the LLM-judge steps call a model per trace/example. For a big room, use
`--deterministic-only` on `score_traces.py` / `monitor.py` for the free fast path,
and keep dataset/trace counts modest.
