from __future__ import annotations

import time
from typing import Any

from core.engine.cache import ReadThroughCache, StagingStore
from core.engine.tools import ToolContext, query_tool, recorder_tool
from core.persistence.recorder import RecorderService
from core.services.query_service import QueryServiceFacade
from core.services.recorder_service import RecorderServiceFacade


class FakeCache:
    def __init__(self):
        self.store: dict[str, Any] = {}
        self.cleared = 0

    def make_key(self, method: str, params: dict[str, Any]) -> str:
        return f"k:{method}:{sorted(params.items())}"

    def get(self, key: str) -> Any | None:
        return self.store.get(key)

    def set(self, key: str, value: Any) -> None:
        self.store[key] = value

    def clear(self) -> None:
        self.cleared += 1
        self.store.clear()


class FakeStaging:
    def __init__(self):
        self.staged: list[dict[str, Any]] = []

    def stage(self, deltas: dict[str, Any]) -> None:
        self.staged.append(deltas)


class QImpl:
    def __init__(self):
        self.calls = 0

    def relations_effective_in_scene(self, scene_id: str):
        self.calls += 1
        return [{"a": "e1", "b": "e2", "type": "ally", "sid": scene_id}]


class RecImpl:
    def __init__(self):
        self.calls = 0

    def commit_deltas(self, **kwargs: Any):
        self.calls += 1
        return {"ok": True, "written": {"facts": len(kwargs.get("facts") or [])}, "warnings": []}


def test_query_tool_uses_cache():
    qs = QueryServiceFacade(QImpl())
    cache = FakeCache()
    ctx = ToolContext(query_service=qs, read_cache=cache)
    out1 = query_tool(ctx, "relations_effective_in_scene", scene_id="s1")
    out2 = query_tool(ctx, "relations_effective_in_scene", scene_id="s1")
    assert out1 == out2 and cache.store  # cached on second call


def test_recorder_tool_dry_run_stages_and_clears_cache():
    qs = QueryServiceFacade(QImpl())
    cache = FakeCache()
    staging = FakeStaging()
    ctx = ToolContext(query_service=qs, read_cache=cache, staging=staging)
    out = recorder_tool(ctx, draft="x", deltas={"facts": [{"description": "d"}]})
    assert out["mode"] == "dry_run" and staging.staged and cache.cleared == 1


def test_recorder_tool_commit_clears_cache():
    rec = RecorderServiceFacade(RecImpl())
    cache = FakeCache()
    ctx = ToolContext(
        query_service=QueryServiceFacade(QImpl()), recorder=rec, read_cache=cache, dry_run=False
    )
    out = recorder_tool(ctx, draft="x", deltas={"facts": [{"description": "d"}]})
    assert out["mode"] == "commit" and cache.cleared == 1


class DummyQueryService:
    def __init__(self):
        self.count = 0

    def relations_effective_in_scene(self, scene_id: str):
        self.count += 1
        return [{"scene": scene_id, "n": self.count}]


class FakeRepo:
    def __init__(self):
        self.calls = []

    def run(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return []


def test_read_through_cache_hits_and_expires(tmp_path):
    cache = ReadThroughCache(capacity=8, ttl_seconds=0.05)
    ctx = ToolContext(query_service=DummyQueryService(), read_cache=cache, dry_run=True)
    r1 = query_tool(ctx, "relations_effective_in_scene", scene_id="S1")
    r2 = query_tool(ctx, "relations_effective_in_scene", scene_id="S1")
    assert r1 and r2
    assert r1[0]["n"] == 1
    assert r2[0]["n"] == 1  # cached
    time.sleep(0.06)
    r3 = query_tool(ctx, "relations_effective_in_scene", scene_id="S1")
    assert r3[0]["n"] == 2


def test_staging_and_flush(tmp_path):
    staging_dir = tmp_path / "staging"
    ctx = ToolContext(
        query_service=DummyQueryService(),
        dry_run=True,
        staging=StagingStore(dirpath=staging_dir),
        read_cache=ReadThroughCache(),
    )
    res1 = recorder_tool(
        ctx, draft="", deltas={"new_entities": [{"name": "Jimmy"}], "universe_id": "U-1"}
    )
    res2 = recorder_tool(
        ctx, draft="", deltas={"new_scene": {"story_id": "ST-1", "sequence_index": 3}}
    )
    assert res1["mode"] == "dry_run" and res2["mode"] == "dry_run"
    assert ctx.staging.pending() == 2
    rec = RecorderService(FakeRepo())
    flush_res = ctx.staging.flush(rec, clear_after=True)
    assert flush_res["ok"] is True
    assert ctx.staging.pending() == 0
