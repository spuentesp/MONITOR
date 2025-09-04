from __future__ import annotations
import pytest
pytestmark = pytest.mark.unit

from core.generation.providers import select_llm_from_env


def test_select_llm_default_mock(monkeypatch):
    monkeypatch.delenv("MONITOR_LLM_BACKEND", raising=False)
    llm = select_llm_from_env()
    # MockLLM has a simple complete method
    out = llm.complete(system_prompt="s", messages=[{"role": "user", "content": "hi"}])
    assert isinstance(out, str)


def test_select_llm_openai_misconfigured_returns_mock(monkeypatch):
    monkeypatch.setenv("MONITOR_LLM_BACKEND", "openai")
    monkeypatch.delenv("MONITOR_OPENAI_API_KEY", raising=False)
    llm = select_llm_from_env()
    out = llm.complete(system_prompt="s", messages=[{"role": "user", "content": "hi"}])
    assert isinstance(out, str)


def test_import_ports_llm_module_executes():
    # Importing ensures top-level class definitions are executed for coverage
    import core.ports.llm as ports_llm  # noqa: F401
