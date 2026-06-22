"""Pytest fixtures/config for the CI module.

Two jobs, both done at import (before tests are collected):
  1. Put the repo root on sys.path so `import hr_agent`, `import config`, and the
     `module_*` packages resolve no matter where pytest is invoked from.
  2. Enable LangSmith tracing by default. The langsmith pytest plugin's
     `t.log_inputs/log_outputs/log_feedback` helpers raise unless
     LANGSMITH_TRACING is 'true', so we set it here (without clobbering an
     explicit value the user already exported).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# 1. Repo root importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 2. Tracing on by default for the langsmith pytest integration.
os.environ.setdefault("LANGSMITH_TRACING", "true")

# Load .env (LANGSMITH_API_KEY etc.) the same way the rest of the workshop does.
import config  # noqa: E402,F401  (import side effect: load_dotenv)
