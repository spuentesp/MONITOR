from __future__ import annotations

import builtins

from core.engine.langgraph_flow import select_engine_backend
from core.engine.orchestrator import run_once
import pytest


def test_select_engine_backend_defaults_to_langgraph(monkeypatch):
    monkeypatch.delenv("MONITOR_ENGINE_BACKEND", raising=False)
    assert select_engine_backend() == "langgraph"


def test_run_once_langgraph_missing_module_raises(monkeypatch):
    # Ensure default requests langgraph, but fail import of langgraph_flow and expect RuntimeError
    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name.startswith("core.engine.langgraph_flow"):
            raise ImportError("no langgraph_flow")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(RuntimeError):
        _ = run_once("hello", scene_id=None, mode="copilot")
