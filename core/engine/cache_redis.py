from __future__ import annotations

import hashlib
import json
import time
from typing import Any

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None


def _json_key(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


class RedisReadThroughCache:
    def __init__(self, url: str, namespace: str = "monitor:cache", ttl_seconds: float = 60.0):
        if redis is None:
            raise RuntimeError("redis-py is not installed. pip install redis")
        self.r = redis.Redis.from_url(url, decode_responses=True)
        self.ns = namespace
        self.ttl = int(ttl_seconds)

    def _ver_key(self) -> str:
        return f"{self.ns}:ver"

    def _version(self) -> str:
        v = self.r.get(self._ver_key())
        return v if v is not None else "0"

    def make_key(self, method: str, params: dict[str, Any]) -> str:
        slug = f"{method}:{_hash(_json_key(params))}"
        return f"{self.ns}:v{self._version()}:{slug}"

    def get(self, key: str) -> Any | None:
        raw = self.r.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return raw

    def set(self, key: str, value: Any) -> None:
        self.r.setex(key, self.ttl, json.dumps(value, ensure_ascii=False))

    def clear(self) -> None:
        # Global invalidation: bump version
        self.r.incr(self._ver_key())


class RedisStagingStore:
    def __init__(self, url: str, list_key: str = "monitor:staging", daily: bool = True):
        if redis is None:
            raise RuntimeError("redis-py is not installed. pip install redis")
        self.r = redis.Redis.from_url(url, decode_responses=True)
        self.base_key = list_key
        self.daily = daily

    def _key(self) -> str:
        if not self.daily:
            return self.base_key
        return f"{self.base_key}:{time.strftime('%Y%m%d')}"

    def stage(self, deltas: dict[str, Any]) -> None:
        self.r.rpush(self._key(), json.dumps(deltas, ensure_ascii=False))

    def pending(self) -> int:
        return int(self.r.llen(self._key()))

    def clear(self) -> None:
        self.r.delete(self._key())

    def flush(self, recorder, clear_after: bool = True) -> dict[str, Any]:
        pipe = self.r.pipeline()
        k = self._key()
        pipe.lrange(k, 0, -1)
        if clear_after:
            pipe.delete(k)
        data, *_ = pipe.execute()
        written_total: dict[str, int] = {}
        warnings: list[str] = []
        ok = True
        for raw in data:
            payload = json.loads(raw)
            res = recorder.commit_deltas(**payload)
            ok = ok and bool(res.get("ok"))
            for k2, v in (res.get("written") or {}).items():
                written_total[k2] = written_total.get(k2, 0) + int(v or 0)
            warnings.extend(res.get("warnings") or [])
        return {"ok": ok, "written": written_total, "warnings": warnings}
