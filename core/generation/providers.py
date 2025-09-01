from __future__ import annotations

import os
from typing import List, Dict, Any, Optional

from core.generation.interfaces.llm import LLM, Message
from core.generation.mock_llm import MockLLM


class OpenAIChat(LLM):
    """OpenAI-compatible chat backend.

    Honors OPENAI_API_KEY or MONITOR_OPENAI_API_KEY; optional MONITOR_OPENAI_BASE_URL (for Azure/OpenRouter/compat).
    Model via MONITOR_OPENAI_MODEL (default: gpt-4o-mini).
    """

    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None):
        try:
            # Local import to avoid hard dependency if not used
            from openai import OpenAI  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("openai package not installed; pip install openai") from e
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = OpenAI(**kwargs)  # type: ignore
        self._model = model

    def complete(
        self,
        *,
        system_prompt: str,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 400,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        msgs = [{"role": "system", "content": system_prompt}] + [
            {"role": m["role"], "content": m["content"]} for m in messages
        ]
        resp = self._client.chat.completions.create(  # type: ignore
            model=self._model,
            messages=msgs,
            temperature=temperature,
            max_tokens=max_tokens,
            **({} if extra is None else extra),
        )
        return resp.choices[0].message.content or ""  # type: ignore


def select_llm_from_env() -> LLM:
    backend = os.getenv("MONITOR_LLM_BACKEND", "mock").lower()
    if backend == "openai":
        api_key = os.getenv("MONITOR_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        model = os.getenv("MONITOR_OPENAI_MODEL", "gpt-4o-mini")
        base_url = os.getenv("MONITOR_OPENAI_BASE_URL")
        if not api_key:
            # Fallback to mock if misconfigured
            return MockLLM()
        try:
            return OpenAIChat(api_key=api_key, model=model, base_url=base_url)
        except Exception:
            return MockLLM()
    # default mock
    return MockLLM()
