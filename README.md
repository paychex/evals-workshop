# Evaluations Workshop — from Fundamentals to Production

A hands-on, progressive introduction to evaluating LLM applications, built
around a single example app: an **HR Onboarding agent**. You learn the app
once, then spend the rest of the workshop on evaluation technique — from a
first single-turn eval all the way to monitoring evals in production.

Stack: **Python + LangChain (`create_agent`) + LangSmith**.

The workshop runs in two sessions:

- **Session 1 — Foundations (Modules 1–4):** what an eval is, single-turn and
  agent evals, and gating a PR with an offline suite.
- **Session 2 — Evals for Production (Modules 5–7):** online evals on live
  traces, improving evaluators with annotation + few-shot, and monitoring
  production for quality drift.

---

## Who this is for

Development teams meeting evaluations for the first time. We start with
concepts and build up. No prior eval experience assumed; basic Python and
comfort with the command line is enough.

## The arc

```
SESSION 1 — Foundations                                    SESSION 2 — Evals for Production
Module 1          Module 2            Module 3          Module 4   │  Module 5            Module 6              Module 7
Fundamentals  ->  Single-turn evals -> Agent evals  ->  Evals in   │  Online evals    ->  Improving evals   ->  Production
(the 4 parts)     (judge the answer)  (the process)     CI (gate)  │  (live traces)       (annotate+few-shot)    monitor (drift)
```

### Session 1 — Foundations

| Module | You learn to… | Evaluators introduced |
|--------|---------------|------------------------|
| **[1 — Fundamentals](module_1_fundamentals/)** | Name the 4 parts of any eval; run one end-to-end. | first deterministic check |
| **[2 — Single-turn](module_2_single_turn/)** | Judge a single answer. | deterministic (facts, **shape validation**) + LLM-judge (correctness, groundedness, tone) |
| **[3 — Agent evals](module_3_agent_evals/)** | Judge the *trajectory* and tool calls, not just the answer. | trajectory (exact / required / forbidden / efficiency), tool-args, LLM trajectory judge |
| **[4 — CI](module_4_ci/)** | Gate a build on eval results. | pytest per-example gate + aggregate threshold gate + GitHub Actions |

### Session 2 — Evals for Production

| Module | You learn to… | What's new |
|--------|---------------|------------|
| **[5 — Online evals](module_5_online_evals/)** | Tell offline experiments from online evals; score *live traces* with no ground truth. | reference-free evaluators, scoring traces + writing feedback, the data flywheel |
| **[6 — Improving evals](module_6_improving_evals/)** | Align an LLM judge to your humans. | annotation queues, "evaluate the evaluator", **few-shot judge alignment** |
| **[7 — Production CI](module_7_production_ci/)** | Monitor production for quality drift. | scheduled monitor, baseline/drift alerting, scheduled GitHub Actions |

The same HR agent (`hr_agent/`) is the system-under-test in every module.

## The example app — HR Onboarding agent

Lives in [`hr_agent/`](hr_agent/). A tool-calling agent that:
- answers HR **policy/benefits questions** (single-turn material), and
- performs **onboarding actions** — provisioning accounts, ordering equipment,
  scheduling orientation (multi-step trajectory material).

Tools are deterministic (they read static mock data), so the same input always
produces the same tool output. That reproducibility is what makes evaluation
meaningful — you measure the *model's* behavior, not flaky downstream systems.

---

## Setup

```bash
# 1. Python 3.10+ and a virtualenv
python -m venv .venv && source .venv/bin/activate

# 2. Install
pip install -r requirements.txt

# 3. Configure keys
cp .env.example .env      # then edit: LANGSMITH_API_KEY + ANTHROPIC_API_KEY
```

You need:
- a **LangSmith API key** (smith.langchain.com → Settings → API Keys), and
- an **Anthropic API key** (or set `WORKSHOP_MODEL=openai:gpt-4o-mini` and an
  `OPENAI_API_KEY` — see `config.py` / `.env.example`).

### Smoke test (no keys needed)

The deterministic evaluators self-test as pure functions:

```bash
python module_2_single_turn/deterministic_evals.py
python module_3_agent_evals/trajectory_evals.py
python module_3_agent_evals/tool_evals.py
python module_5_online_evals/reference_free_evals.py
```

### Run a module (keys needed)

```bash
# Session 1 — offline experiments
python module_1_fundamentals/01_first_eval.py
python module_2_single_turn/run_eval.py
python module_3_agent_evals/run_eval.py
python module_4_ci/ci_gate.py --suite agent

# Session 2 — production evals
python module_5_online_evals/production_traffic.py   # create live traces
python module_5_online_evals/score_traces.py         # online-eval loop
python module_6_improving_evals/judge_alignment.py   # zero-shot vs few-shot
python module_7_production_ci/monitor.py             # drift vs baseline
```

Each prints a link/name to open the experiment (or project) in LangSmith.

---

## Repo map

```
hr_agent/                  # the system under test (agent + tools + mock data)
# --- Session 1: Foundations ---
module_1_fundamentals/     # concepts + first eval
module_2_single_turn/      # deterministic + LLM-judge evaluators
module_3_agent_evals/      # trajectory + tool evaluators
module_4_ci/               # pytest gate, aggregate gate, GitHub Actions
# --- Session 2: Evals for Production ---
module_5_online_evals/     # reference-free evals + scoring live traces
module_6_improving_evals/  # annotation queues + few-shot judge alignment
module_7_production_ci/    # scheduled drift monitor + baseline
.github/workflows/evals.yml         # offline gate (PR)
.github/workflows/online-evals.yml  # online monitor (scheduled)
config.py                  # model + LangSmith config (one place to swap providers)
```
