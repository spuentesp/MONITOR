from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

import sys
import types

from core.generation.providers import OpenAIChat


class _Msg:
    def __init__(self, content: str):
        self.content = content


class _Choice:
    def __init__(self, content: str):
        self.message = _Msg(content)


class _Resp:
    def __init__(self, content: str):
        self.choices = [_Choice(content)]


class _Completions:
    def create(self, **_kwargs):
        return _Resp("ok")


class _Chat:
    def __init__(self):
        self.completions = _Completions()


class _Client:
    def __init__(self, **_kwargs):
        self.chat = _Chat()


def test_openai_chat_with_fake_module(monkeypatch):
    # Install a fake openai module providing OpenAI
    fake_mod = types.SimpleNamespace(OpenAI=_Client)
    sys.modules["openai"] = fake_mod
    try:
        cli = OpenAIChat(api_key="k", model="m")
        out = cli.complete(system_prompt="s", messages=[{"role": "user", "content": "x"}])
        assert out == "ok"
    finally:
        sys.modules.pop("openai", None)
