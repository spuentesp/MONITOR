from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from queue import Empty, Queue
from threading import Event, Thread
import time
from typing import Any

DeciderFn = Callable[[dict[str, Any]], tuple[bool, str]]


def default_decider(payload: dict[str, Any]) -> tuple[bool, str]:
    """Return (should_commit, reason) using simple heuristics.

    Heuristics:
    - Commit on structural writes (new_* keys, relations/relation_states present).
    - Commit if 2+ facts provided.
    - Commit if any fact description contains strong change keywords.
    """
    deltas = payload.get("deltas") or {}
    draft = (payload.get("draft") or "").lower()

    # Structural signals
    structural_keys = (
        "new_multiverse",
        "new_universe",
        "new_arc",
        "new_story",
        "new_scene",
        "new_entities",
        "relations",
        "relation_states",
    )
    if any(k in deltas and deltas.get(k) for k in structural_keys):
        return True, "structural_change"

    facts = deltas.get("facts") or []
    if isinstance(facts, list) and len(facts) >= 2:
        return True, "batch_facts"

    # Strong-change keywords
    text_blobs: list[str] = []
    for f in facts:
        if isinstance(f, dict):
            d = f.get("description")
            if isinstance(d, str):
                text_blobs.append(d.lower())
    text_blobs.append(draft)
    txt = "\n".join(text_blobs)
    strong = (
        " kill ",
        " killed",
        " dies",
        " dead",
        " death",
        " marry",
        " married",
        " divorce",
        " betray",
        " broke up",
        " break up",
        " destroyed",
        " destroyed",
        " birth",
        " born",
    )
    if any(kw in txt for kw in strong):
        return True, "strong_change_keyword"

    return False, "low_significance"


@dataclass
class AutoCommitWorker:
    queue: Queue
    recorder: Any
    read_cache: Any | None = None
    idempotency: set[str] | None = None
    decider: DeciderFn = default_decider
    # Stats for UI/monitoring
    committed_count: int = 0
    skipped_count: int = 0
    last_reason: str | None = None
    last_committed_at: float | None = None
    last_error: str | None = None
    last_run_id: str | None = None

    def __post_init__(self):
        self._stop = Event()
        self._thread: Thread | None = None

    def start(self, daemon: bool = True) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = Thread(target=self._run, name="monitor-autocommit", daemon=daemon)
        self._thread.start()

    def stop(self, timeout: float | None = None) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                item = self.queue.get(timeout=0.25)
            except Empty:
                continue
            try:
                key = item.get("delta_key") or ""
                if self.idempotency is not None and key in self.idempotency:
                    self.skipped_count += 1
                    self.last_reason = "idempotent_skip"
                    continue
                should_commit, reason = self.decider(item)
                if not should_commit:
                    self.skipped_count += 1
                    self.last_reason = reason
                    continue
                deltas = item.get("deltas") or {}
                self.recorder.commit_deltas(
                    scene_id=deltas.get("scene_id"),
                    facts=deltas.get("facts"),
                    relation_states=deltas.get("relation_states"),
                    relations=deltas.get("relations"),
                    universe_id=deltas.get("universe_id"),
                    new_multiverse=deltas.get("new_multiverse"),
                    new_universe=deltas.get("new_universe"),
                    new_arc=deltas.get("new_arc"),
                    new_story=deltas.get("new_story"),
                    new_scene=deltas.get("new_scene"),
                    new_entities=deltas.get("new_entities"),
                )
                if self.idempotency is not None:
                    self.idempotency.add(key)
                self.last_reason = reason
                self.last_committed_at = time.time()
                self.last_run_id = key
                self.committed_count += 1
                try:
                    if self.read_cache is not None:
                        self.read_cache.clear()
                except Exception:
                    pass
            except Exception:
                # Swallow and keep running
                self.last_error = "commit_error"
            finally:
                try:
                    self.queue.task_done()
                except Exception:
                    pass

    def get_stats(self) -> dict[str, Any]:
        """Return a compact status dict for UI panels."""
        depth = None
        try:
            depth = self.queue.qsize()
        except Exception:
            depth = None
        last_at = None
        if self.last_committed_at is not None:
            try:
                last_at = time.strftime("%H:%M:%S", time.localtime(self.last_committed_at))
            except Exception:
                last_at = self.last_committed_at
        return {
            "queue_depth": depth,
            "committed": self.committed_count,
            "skipped": self.skipped_count,
            "last_reason": self.last_reason,
            "last_committed_at": last_at,
            "last_run_id": self.last_run_id,
            "last_error": self.last_error,
        }
