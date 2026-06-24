"""Shared configuration for the evals workshop.

One place to control which model powers the agent and the LLM judges, so the
whole workshop can swap providers by changing a single env var.
"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

# Load .env once, on import, for every script in the workshop.
# override=True makes the workshop's .env authoritative over ambient shell/IDE
# environment variables. This matters because some shells/IDEs export keys like
# ANTHROPIC_API_KEY as an EMPTY string; plain load_dotenv() treats an empty
# ambient value as "already set" and silently skips the real key in .env,
# which then surfaces as a confusing 403 from the model provider/gateway.
load_dotenv(override=True)

# init_chat_model string form: just the model name; the provider is supplied
# separately via MODEL_PROVIDER below (Paychex MaaS routes OpenAI/Azure models).
DEFAULT_MODEL = "gpt-5.4-mini"

# Provider used by aipe's MaaS wrappers. Azure OpenAI hosts our OpenAI models.
MODEL_PROVIDER = os.getenv("WORKSHOP_MODEL_PROVIDER", "azure_openai")

# The agent under test. Override with WORKSHOP_MODEL.
AGENT_MODEL = os.getenv("WORKSHOP_MODEL", DEFAULT_MODEL)

# The model that grades outputs in LLM-as-judge evaluators. Judges can be a
# different (often cheaper) model than the agent. Override with
# WORKSHOP_JUDGE_MODEL, else falls back to the agent model.
JUDGE_MODEL = os.getenv("WORKSHOP_JUDGE_MODEL", AGENT_MODEL)


@lru_cache(maxsize=None)
def get_judge(model: str = JUDGE_MODEL):
    """Return a chat model for use in LLM-as-judge evaluators.

    Temperature 0 for the most deterministic grading we can get. Cached so
    repeated evaluator calls reuse one client.
    """
    from aipe import init_payx_chat_model

    return init_payx_chat_model(model, model_provider=MODEL_PROVIDER, temperature=0)


def require_langsmith() -> None:
    """Fail fast with a friendly message if LangSmith isn't configured."""
    if not os.getenv("LANGSMITH_API_KEY"):
        raise SystemExit(
            "LANGSMITH_API_KEY is not set. Copy .env.example to .env and add "
            "your key, or `export LANGSMITH_API_KEY=...`. Get one at "
            "https://smith.langchain.com → Settings → API Keys."
        )
