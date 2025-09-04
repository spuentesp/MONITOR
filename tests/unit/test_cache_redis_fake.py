from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

import types

import core.engine.cache_redis as cr


class FakeRedis:
    def __init__(self):
        self.kv: dict[str, str] = {}
        self.lists: dict[str, list[str]] = {}

    @classmethod
    def from_url(cls, *_args, **_kwargs):
        return cls()

    def get(self, k: str):
        return self.kv.get(k)

    def setex(self, k: str, _ttl: int, v: str):
        self.kv[k] = v

    def incr(self, k: str):
        v = int(self.kv.get(k, "0")) + 1
        self.kv[k] = str(v)
        return v

    def rpush(self, k: str, v: str):
        self.lists.setdefault(k, []).append(v)

    def llen(self, k: str) -> int:
        return len(self.lists.get(k, []))

    def delete(self, k: str):
        self.llists = self.lists
        self.lists.pop(k, None)

    def lrange(self, k: str, start: int, end: int):
        data = self.lists.get(k, [])
        return data[start : (end + 1 if end != -1 else None)]

    # Simple pipeline that batches lrange and delete
    def pipeline(self):
        self._pipe_cmds = []

        class Pipe:
            def __init__(self, outer: FakeRedis):
                self.outer = outer
                self.cmds: list[tuple[str, tuple, dict]] = []

            def lrange(self, *a, **kw):
                self.cmds.append(("lrange", a, kw))

            def delete(self, *a, **kw):
                self.cmds.append(("delete", a, kw))

            def execute(self):
                results = []
                for name, a, kw in self.cmds:
                    if name == "lrange":
                        results.append(self.outer.lrange(*a, **kw))
                    elif name == "delete":
                        self.outer.delete(*a, **kw)
                        results.append(1)
                return results

        return Pipe(self)


def test_redis_cache_and_staging_with_fake(monkeypatch):
    # Install fake redis module
    fake_mod = types.SimpleNamespace(Redis=FakeRedis)
    monkeypatch.setattr(cr, "redis", fake_mod, raising=True)

    cache = cr.RedisReadThroughCache(url="redis://fake", ttl_seconds=1)
    key = cache.make_key("m", {"a": 1})
    assert cache.get(key) is None
    cache.set(key, {"x": 2})
    assert cache.get(key) == {"x": 2}
    cache.clear()
    # After clear, version bump causes different key; still ensure no crash
    key2 = cache.make_key("m", {"a": 1})
    assert key != key2

    staged = cr.RedisStagingStore(url="redis://fake", list_key="k")
    staged.stage({"scene_id": "s1", "facts": []})
    assert staged.pending() == 1

    class Rec:
        def commit_deltas(self, **payload):
            return {
                "ok": True,
                "written": {"facts": len(payload.get("facts") or [])},
                "warnings": [],
            }

    res = staged.flush(Rec(), clear_after=True)
    assert res["ok"] is True and res["written"].get("facts", 0) >= 0
