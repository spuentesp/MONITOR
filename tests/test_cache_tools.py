import time

from core.engine.cache import ReadThroughCache, StagingStore
from core.engine.tools import ToolContext, query_tool, recorder_tool
from core.persistence.recorder import RecorderService


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
