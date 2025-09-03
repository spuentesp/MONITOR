from __future__ import annotations
import pytest
pytestmark = pytest.mark.unit

import sys
import types

from core.engine.lc_tools import build_langchain_tools
from core.engine.tools import ToolContext


def test_build_langchain_tools_happy(monkeypatch):
    # Fake Tool class compatible with build_langchain_tools expectations
    class FakeTool:
        def __init__(self, name, func):
            self.name = name
            self.func = func

        def invoke(self, params: dict):
            # LangChain usually maps dict -> kwargs
            return self.func(**params)

        @classmethod
        def from_function(cls, name: str, description: str, func):  # type: ignore[override]
            return cls(name=name, func=func)

    fake_mod = types.SimpleNamespace(Tool=FakeTool)
    sys.modules["langchain_core.tools"] = fake_mod

    class Q:
        def relations_effective_in_scene(self, scene_id: str):
            return [{"a": 1}]

        def entities_in_scene(self, scene_id: str):
            return [{"id": "e1"}]

        def facts_for_scene(self, scene_id: str):
            return [{"description": "d"}]

    calls = {"rec": 0}

    def fake_recorder_tool(ctx: ToolContext, draft: str, deltas: dict):
        calls["rec"] += 1
        return {"ok": True, "mode": "dry_run", "deltas": deltas}

    monkeypatch.setattr("core.engine.tools.recorder_tool", fake_recorder_tool)
    ctx = ToolContext(query_service=Q())
    tools = build_langchain_tools(ctx)
    names = {t.name for t in tools}
    assert {"query_tool", "rules_tool", "recorder_tool"}.issubset(names)

    # Use query tool via invoke mapping
    qt = next(t for t in tools if t.name == "query_tool")
    out = qt.invoke({"method": "relations_effective_in_scene", "scene_id": "s1"})
    assert out and isinstance(out, list)

    # Recorder tool should call our fake recorder
    rt = next(t for t in tools if t.name == "recorder_tool")
    r = rt.invoke({"draft": "x", "scene_id": "s1"})
    assert calls["rec"] == 1 and r.get("ok")

    # Rules tool returns a stub dict
    ru = next(t for t in tools if t.name == "rules_tool")
    rv = ru.invoke({"action": "check", "foo": 1})
    assert rv.get("result") == "partial"
