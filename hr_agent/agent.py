"""The HR Onboarding agent, built with langchain's create_agent.

A single-purpose tool-calling agent: it answers new-hire policy questions and
performs onboarding actions (provisioning accounts/equipment, scheduling
orientation). create_agent runs the standard ReAct loop (model -> tools ->
model -> ...), which is exactly what we want to evaluate.
"""

from __future__ import annotations

from aipe import create_payx_agent

from config import AGENT_MODEL, MODEL_PROVIDER
from hr_agent.tools import HR_TOOLS

SYSTEM_PROMPT = """You are the HR Onboarding Assistant for a mid-size company.

You help new hires and the people team with two kinds of requests:
1. Answering HR policy and benefits questions.
2. Performing onboarding actions: provisioning IT accounts, ordering
   equipment, and scheduling orientation.

Guidelines:
- For policy questions, ALWAYS call lookup_hr_policy and ground your answer in
  the returned text. Never invent policy numbers or dates.
- For onboarding actions, you usually need an employee_id. Call
  lookup_employee first to get it, then perform the requested actions.
- Be concise, warm, and professional. New hires are your audience.
- If a request is ambiguous or an employee can't be found, say so rather than
  guessing.
"""


def build_agent(model: str = AGENT_MODEL):
    """Construct the HR onboarding agent. Returns a compiled LangGraph app."""
    return create_payx_agent(
        model=model,
        tools=HR_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        model_kwargs={"model_provider": MODEL_PROVIDER},
    )


def run_agent(question: str, model: str = AGENT_MODEL) -> dict:
    """Run the agent on a single user message and return the raw result.

    The result is the standard create_agent output: ``{"messages": [...]}``.
    Downstream evaluators read both the final message and the tool-call
    trajectory from this. See hr_agent/trajectory.py for the extractors.
    """
    agent = build_agent(model)
    return agent.invoke({"messages": [("user", question)]})


if __name__ == "__main__":
    # Quick manual smoke test: `python -m hr_agent.agent`
    result = run_agent("How many vacation days do new employees get?")
    print(result["messages"][-1].content)
