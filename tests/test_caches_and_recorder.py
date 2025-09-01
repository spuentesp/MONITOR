from __future__ import annotations

import pytest

from core.engine.cache_redis import RedisReadThroughCache, RedisStagingStore
from core.persistence.recorder import RecorderService


def test_redis_classes_raise_without_dependency():
    with pytest.raises(RuntimeError):
        RedisReadThroughCache(url="redis://localhost:6379/0")
    with pytest.raises(RuntimeError):
        RedisStagingStore(url="redis://localhost:6379/0")


class FakeRepo:
    def __init__(self):
        self.queries: list[str] = []

    def run(self, q: str, **params):
        self.queries.append(q)
        # Return empty or simple rows for queries that expect return value
        if "RETURN collect(e.id) AS ids" in q:
            return [{"ids": []}]
        return []


def test_recorder_commit_minimal_entities_and_scene():
    repo = FakeRepo()
    svc = RecorderService(repo)
    res = svc.commit_deltas(
        universe_id="u1",
        new_entities=[{"id": "e1", "name": "N", "attributes": {}, "type": "pc"}],
        new_scene={"id": "s1", "story_id": None, "participants": ["e1"]},
    )
    assert res["ok"] and res["written"]["entities"] == 1 and res["written"]["scenes"] == 1
