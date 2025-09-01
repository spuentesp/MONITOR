from __future__ import annotations

import core.generation.providers as providers


def test_select_llm_openai_instantiation_error_fallback(monkeypatch):
    monkeypatch.setenv("MONITOR_LLM_BACKEND", "openai")
    monkeypatch.setenv("MONITOR_OPENAI_API_KEY", "sk-xyz")
    monkeypatch.setenv("MONITOR_OPENAI_MODEL", "gpt-4o-mini")

    class Boom:
        def __init__(self, *_, **__):  # pragma: no cover - simple test double
            raise RuntimeError("openai missing")

    # Force OpenAIChat to fail so select_llm_from_env falls back to MockLLM
    monkeypatch.setattr(providers, "OpenAIChat", Boom)
    llm = providers.select_llm_from_env()
    out = llm.complete(system_prompt="s", messages=[{"role": "user", "content": "hi"}])
    assert isinstance(out, str)
