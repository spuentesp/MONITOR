from __future__ import annotations
import pytest
pytestmark = pytest.mark.unit

from dataclasses import dataclass
from typing import Any

from core.engine.tools import ToolContext, query_tool, recorder_tool
from core.services.query_service import QueryServiceFacade
from core.services.recorder_service import RecorderServiceFacade


@dataclass
class FakeRepo:
    def run(self, _q: str, **_p: Any):  # minimal duck type
        return []


class FakeQueryImpl:
    def __init__(self):
        self.called: list[str] = []

    def relations_effective_in_scene(self, scene_id: str):
        self.called.append(scene_id)
        return [{"a": "e1", "b": "e2", "type": "ally"}]


class FakeRecorderImpl:
    def __init__(self):
        self.calls: list[dict[str, Any]] = []

    def commit_deltas(self, **kwargs: Any):
        self.calls.append(kwargs)
        return {"ok": True, "written": {"facts": len(kwargs.get("facts") or [])}, "warnings": []}


def test_query_facade_and_tool():
    qs = QueryServiceFacade(FakeQueryImpl())
    ctx = ToolContext(query_service=qs)
    out = query_tool(ctx, "relations_effective_in_scene", scene_id="s1")
    assert out and out[0]["type"] == "ally"


def test_recorder_tool_dry_run_stages_when_no_recorder():
    ctx = ToolContext(query_service=QueryServiceFacade(FakeQueryImpl()))
    out = recorder_tool(ctx, draft="x", deltas={"facts": [{"description": "d"}]})
    assert out["mode"] == "dry_run"


def test_recorder_tool_commit_when_recorder_present():
    rec = RecorderServiceFacade(FakeRecorderImpl())
    ctx = ToolContext(
        query_service=QueryServiceFacade(FakeQueryImpl()), recorder=rec, dry_run=False
    )
    out = recorder_tool(ctx, draft="x", deltas={"facts": [{"description": "d"}]})
    assert out["mode"] == "commit" and out["result"]["ok"]
