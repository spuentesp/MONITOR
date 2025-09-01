from __future__ import annotations

import builtins

import pytest

from core.engine.lc_tools import build_langchain_tools


def test_build_langchain_tools_raises_without_langchain(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name.startswith("langchain_core"):
            raise ImportError("no langchain")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(RuntimeError):
        build_langchain_tools(object())
