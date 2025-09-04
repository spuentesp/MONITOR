from __future__ import annotations

import os
from pathlib import Path
import sys


def _ensure_repo_root_on_path() -> None:
    # tests/ -> repo root
    root = Path(__file__).resolve().parents[1]
    p = str(root)
    if p not in sys.path:
        sys.path.insert(0, p)


_ensure_repo_root_on_path()

# Test runtime environment hardening: force fast, offline, deterministic behavior
# - Use MockLLM (no network) regardless of developer env
# - Disable optional background workers and strict health checks
# - Avoid optional LC tools wiring that can import heavy deps
os.environ["MONITOR_LLM_BACKEND"] = "mock"
os.environ["MONITOR_AUTOCOMMIT"] = "0"
os.environ["MONITOR_AGENTIC_STRICT"] = "0"
os.environ["MONITOR_COPILOT_PAUSE"] = "0"
os.environ["MONITOR_LC_TOOLS"] = "0"
os.environ["MONITOR_FORCE_DEMO"] = "1"


# Test helper: build a minimal valid ContextToken header
def make_ctx_header(mode: str = "read") -> dict[str, str]:
    from core.engine.context import ContextToken

    t = ContextToken(omniverse_id="o1", multiverse_id="m1", universe_id="u1", mode=mode)
    return {"X-Context-Token": t.model_dump_json()}
