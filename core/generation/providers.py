from __future__ import annotations

import os
from typing import Any

from core.generation.interfaces.llm import LLM, Message
from core.generation.mock_llm import MockLLM


class OpenAIChat(LLM):
    """OpenAI-compatible chat backend.

    Honors OPENAI_API_KEY or MONITOR_OPENAI_API_KEY; optional MONITOR_OPENAI_BASE_URL (for Azure/OpenRouter/compat).
    Model via MONITOR_OPENAI_MODEL (default: gpt-4o-mini).
    """

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
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
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 400,
        extra: dict[str, Any] | None = None,
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


class GroqChat(LLM):
    """Groq chat backend.

    Uses the groq Python client (pip install groq).
    Model via MONITOR_GROQ_MODEL (must be a supported Groq model).
    """

    def __init__(self, api_key: str, model: str):
        try:
            from groq import (
                Groq,  # type: ignore
            )
        except Exception as e:  # pragma: no cover
            raise RuntimeError("groq package not installed; pip install groq") from e
        self._client = Groq(api_key=api_key)  # type: ignore
        self._model = model
        self._BadRequestError = locals().get("BadRequestError")  # type: ignore

    def complete(
        self,
        *,
        system_prompt: str,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 400,
        extra: dict[str, Any] | None = None,
    ) -> str:
        msgs = [{"role": "system", "content": system_prompt}] + [
            {"role": m["role"], "content": m["content"]} for m in messages
        ]
        try:
            resp = self._client.chat.completions.create(  # type: ignore
                model=self._model,
                messages=msgs,
                temperature=temperature,
                max_tokens=max_tokens,
                **({} if extra is None else extra),
            )
            return resp.choices[0].message.content or ""  # type: ignore
        except Exception as e:  # pragma: no cover - network/client errors
            # Convert common Groq errors into a friendlier message for callers/UI.
            err_msg = str(e)
            try:
                if self._BadRequestError and isinstance(e, self._BadRequestError):  # type: ignore
                    err_msg = (
                        "Groq rejected the request. Check your model selection and parameters: "
                        + err_msg
                    )
            except Exception:
                pass
            raise RuntimeError(err_msg) from e


SUPPORTED_GROQ_MODELS = [
    # Production
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-guard-4-12b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "whisper-large-v3",
    "whisper-large-v3-turbo",
    # Preview (allow but mark as preview)
    "deepseek-r1-distill-llama-70b",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-prompt-guard-2-22m",
    "meta-llama/llama-prompt-guard-2-86m",
    "moonshotai/kimi-k2-instruct",
    "playai-tts",
    "playai-tts-arabic",
    "qwen/qwen3-32b",
    # Preview systems
    "compound-beta",
    "compound-beta-mini",
]


def _validate_groq_model(model: str | None) -> str:
    """Return a model id: respect user choice, map deprecated aliases, or default."""
    default_model = "llama-3.1-8b-instant"
    if not model:
        return default_model
    m = model.strip()
    if m in SUPPORTED_GROQ_MODELS:
        return m
    # Some known deprecations mapping
    deprecated_aliases = {
        "llama3-8b-8192": default_model,
        "llama-3-8b-instant": default_model,
    }
    if m in deprecated_aliases:
        return deprecated_aliases[m]
    # Allow unknown/new models as-is (UI may fetch dynamically)
    return m


def list_groq_models(api_key: str) -> list[str]:
    """Fetch available Groq model IDs dynamically.

    Tries the groq Python client first; falls back to HTTP GET on
    https://api.groq.com/openai/v1/models. Returns an empty list on error.
    """
    # Try groq client SDK
    try:  # pragma: no cover - requires network
        from groq import Groq  # type: ignore

        client = Groq(api_key=api_key)  # type: ignore
        if hasattr(client, "models") and hasattr(client.models, "list"):
            res = client.models.list()  # type: ignore[attr-defined]
            # openai-style: res.data -> list of {id: str, ...}
            data = getattr(res, "data", None) or []
            out = []
            for item in data:
                mid = getattr(item, "id", None) or (
                    item.get("id") if isinstance(item, dict) else None
                )
                if isinstance(mid, str):
                    out.append(mid)
            if out:
                return sorted(out)
    except Exception:
        pass

    # Fallback to raw HTTP via stdlib
    try:  # pragma: no cover - requires network
        import json
        from urllib.request import Request, urlopen

        req = Request(
            "https://api.groq.com/openai/v1/models",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="GET",
        )
        with urlopen(req, timeout=10) as resp:  # nosec B310
            body = resp.read().decode("utf-8")
            payload = json.loads(body)
            data = payload.get("data", [])
            out = [
                x.get("id") for x in data if isinstance(x, dict) and isinstance(x.get("id"), str)
            ]
            if out:
                return sorted(out)
    except Exception:
        pass

    return []


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
    elif backend == "groq":
        api_key = os.getenv("MONITOR_GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
        model = _validate_groq_model(os.getenv("MONITOR_GROQ_MODEL", None))
        if not api_key:
            return MockLLM()
        try:
            return GroqChat(api_key=api_key, model=model)
        except Exception:
            return MockLLM()
    # default mock
    return MockLLM()
