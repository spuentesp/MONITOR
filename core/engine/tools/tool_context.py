"""Tool context for managing shared handles across tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:  # Optional typing only; no runtime import dependency
    from core.ports.cache import CachePort, StagingPort
    from core.ports.storage import QueryReadPort, RecorderWritePort
except Exception:  # pragma: no cover
    CachePort = StagingPort = QueryReadPort = RecorderWritePort = Any  # type: ignore


@dataclass
class ToolContext:
    """Holds shared handles for tools.

    query_service: public read facade for the graph (safe to call).
    rules: optional rules/system helpers loaded from YAML (not implemented yet).
    dry_run: if True, Recorder won't persist; returns a plan/diff instead.
    """

    # Use Any for runtime-injected ports to avoid import-time typing issues
    query_service: Any
    recorder: Any | None = None
    rules: Any | None = None
    dry_run: bool = True
    # Optional caches (duck-typed interfaces)
    read_cache: Any | None = None
    staging: Any | None = None

    # Optional async auto-commit agent wiring (non-blocking)
    autocommit_enabled: bool = False
    autocommit_queue: Any | None = None  # e.g., queue.Queue
    autocommit_worker: Any | None = None  # background thread/worker handle
    # Simple in-memory idempotency set shared with the worker
    idempotency: set[str] | None = None

    # Optional satellite stores (constructed lazily; connect() when used)
    mongo: Any | None = None  # MongoStore
    qdrant: Any | None = None  # QdrantIndex
    opensearch: Any | None = None  # SearchIndex
    minio: Any | None = None  # ObjectStore
    embedder: Any | None = None  # Callable[[str], list[float]]
