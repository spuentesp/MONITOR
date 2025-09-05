from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
import json
from pathlib import Path
import time
from typing import Any


def _json_key(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


@dataclass
class ReadThroughCache:
    capacity: int = 256
    ttl_seconds: float = 60.0
    _store: OrderedDict[str, tuple[Any, float]] = field(default_factory=OrderedDict)

    def _evict_if_needed(self):
        while len(self._store) > self.capacity:
            self._store.popitem(last=False)

    def get(self, key: str) -> Any | None:
        now = time.time()
        item = self._store.get(key)
        if not item:
            return None
        value, expires = item
        if expires < now:
            try:
                del self._store[key]
            except KeyError:
                pass
            return None
        self._store.move_to_end(key, last=True)
        return value

    def set(self, key: str, value: Any) -> None:
        expires = time.time() + self.ttl_seconds
        self._store[key] = (value, expires)
        self._store.move_to_end(key, last=True)
        self._evict_if_needed()

    def clear(self) -> None:
        self._store.clear()

    @staticmethod
    def make_key(method: str, params: dict[str, Any]) -> str:
        return f"{method}:{_json_key(params)}"


@dataclass
class StagingStore:
    dirpath: Path = field(default_factory=lambda: Path("ops/staging"))
    persist: bool = True
    _buffer: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        self.dirpath.mkdir(parents=True, exist_ok=True)

    def stage(self, deltas: dict[str, Any]) -> None:
        self._buffer.append(deltas)
        if self.persist:
            fp = self.dirpath / (time.strftime("%Y%m%d") + ".jsonl")
            with fp.open("a", encoding="utf-8") as f:
                f.write(json.dumps(deltas, ensure_ascii=False) + "\n")

    def flush(self, recorder, clear_after: bool = True) -> dict[str, Any]:
        written_total: dict[str, int] = {}
        warnings: list[str] = []
        ok = True
        for payload in list(self._buffer):
            res = recorder.commit_deltas(**payload)
            ok = ok and bool(res.get("ok"))
            for k, v in (res.get("written") or {}).items():
                written_total[k] = written_total.get(k, 0) + int(v or 0)
            warnings.extend(res.get("warnings") or [])
        if clear_after:
            self._buffer.clear()
        return {"ok": ok, "written": written_total, "warnings": warnings}

    def pending(self) -> int:
        return len(self._buffer)

    def peek_all(self) -> list[dict[str, Any]]:
        """Return all staged items without removing them."""
        return self._buffer.copy()

    def clear(self) -> None:
        self._buffer.clear()
