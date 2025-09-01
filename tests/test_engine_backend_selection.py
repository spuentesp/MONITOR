from __future__ import annotations

import builtins

from core.engine.langgraph_flow import select_engine_backend
from core.engine.orchestrator import run_once


def test_select_engine_backend_defaults_to_inmemory(monkeypatch):
    monkeypatch.delenv("MONITOR_ENGINE_BACKEND", raising=False)
    assert select_engine_backend() == "inmemory"


def test_run_once_langgraph_env_but_missing_module_falls_back(monkeypatch):
    # Force env to request langgraph, but fail import of langgraph_flow to exercise fallback
    monkeypatch.setenv("MONITOR_ENGINE_BACKEND", "langgraph")
    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name.startswith("core.engine.langgraph_flow"):
            raise ImportError("no langgraph_flow")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    out = run_once("hello", scene_id=None, mode="copilot")
    # Should still return in-memory orchestrator result
    assert "draft" in out and "summary" in out and "commit" in out
