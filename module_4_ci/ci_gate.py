"""Module 4 — the CI gate.

Run an experiment over a dataset, aggregate the scores, and EXIT NON-ZERO if
any metric falls below its threshold. That non-zero exit is what fails a CI
build and blocks a regression from merging.

This is the "aggregate gate" pattern: one pass/fail signal for the whole
dataset per metric. (The pytest approach in test_evals.py is the
"per-example gate" alternative — see the README for when to use which.)

Usage:
    python module_4_ci/ci_gate.py --suite single_turn
    python module_4_ci/ci_gate.py --suite agent
    python module_4_ci/ci_gate.py --suite single_turn --threshold 0.9
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langsmith import Client

from config import require_langsmith

# Per-metric pass thresholds. Tune these to your risk tolerance. Safety-style
# metrics (no_forbidden_tools) demand a perfect score; fuzzy quality metrics
# (professional_tone) get more headroom.
THRESHOLDS: dict[str, float] = {
    # single-turn
    "response_not_empty": 1.0,
    "mentions_required_facts": 0.8,
    "no_unsupported_topic": 1.0,
    "correctness": 0.8,
    "groundedness": 0.9,
    "professional_tone": 0.6,
    # agent
    "trajectory_exact_match": 0.5,
    "required_tools_used": 0.9,
    "no_forbidden_tools": 1.0,
    "trajectory_efficiency": 0.7,
    "correct_employee_id": 1.0,
    "tool_args_well_formed": 1.0,
    "trajectory_is_reasonable": 0.8,
}


def build_suite(suite: str):
    """Return (target_fn, dataset_name, evaluators) for the requested suite."""
    if suite == "single_turn":
        from hr_agent import run_agent
        from hr_agent.trajectory import final_response
        from module_2_single_turn.datasets import ensure_dataset, DATASET_NAME
        from module_2_single_turn.deterministic_evals import DETERMINISTIC_EVALUATORS
        from module_2_single_turn.llm_judge_evals import LLM_JUDGE_EVALUATORS

        def target(inputs: dict) -> dict:
            return {"answer": final_response(run_agent(inputs["question"]))}

        ensure_dataset()
        return target, DATASET_NAME, [*DETERMINISTIC_EVALUATORS, *LLM_JUDGE_EVALUATORS]

    if suite == "agent":
        from hr_agent import run_agent
        from hr_agent.trajectory import extract_tool_calls, extract_trajectory, final_response
        from module_3_agent_evals.datasets import ensure_dataset, DATASET_NAME
        from module_3_agent_evals.trajectory_evals import TRAJECTORY_EVALUATORS
        from module_3_agent_evals.tool_evals import TOOL_EVALUATORS
        from module_3_agent_evals.llm_trajectory_judge import LLM_TRAJECTORY_EVALUATORS

        def target(inputs: dict) -> dict:
            result = run_agent(inputs["question"])
            return {
                "trajectory": extract_trajectory(result),
                "tool_calls": extract_tool_calls(result),
                "answer": final_response(result),
            }

        ensure_dataset()
        return target, DATASET_NAME, [
            *TRAJECTORY_EVALUATORS, *TOOL_EVALUATORS, *LLM_TRAJECTORY_EVALUATORS,
        ]

    raise SystemExit(f"Unknown suite '{suite}'. Choose 'single_turn' or 'agent'.")


def aggregate_scores(results) -> dict[str, float]:
    """Mean score per metric across all examples in the experiment."""
    sums: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for row in results:
        for res in row["evaluation_results"]["results"]:
            if res.score is not None:
                sums[res.key] += float(res.score)
                counts[res.key] += 1
    return {key: sums[key] / counts[key] for key in sums}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an eval suite as a CI gate.")
    parser.add_argument("--suite", choices=["single_turn", "agent"], required=True)
    parser.add_argument("--threshold", type=float, default=None,
                        help="Override: apply this single threshold to every metric.")
    args = parser.parse_args()

    require_langsmith()
    client = Client()
    target, dataset_name, evaluators = build_suite(args.suite)

    results = client.evaluate(
        target,
        data=dataset_name,
        evaluators=evaluators,
        experiment_prefix=f"ci-gate-{args.suite}",
        max_concurrency=4,
    )

    means = aggregate_scores(results)

    print(f"\n=== CI gate: {args.suite} ===")
    failures: list[str] = []
    for metric in sorted(means):
        mean = means[metric]
        threshold = args.threshold if args.threshold is not None else THRESHOLDS.get(metric, 0.0)
        passed = mean >= threshold
        flag = "PASS" if passed else "FAIL"
        print(f"  [{flag}] {metric:<26} mean={mean:.3f}  threshold={threshold:.2f}")
        if not passed:
            failures.append(f"{metric} ({mean:.3f} < {threshold:.2f})")

    if failures:
        print(f"\nGATE FAILED — {len(failures)} metric(s) below threshold:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)  # non-zero exit fails the CI build

    print("\nGATE PASSED — all metrics meet their thresholds.")
    sys.exit(0)


if __name__ == "__main__":
    main()
