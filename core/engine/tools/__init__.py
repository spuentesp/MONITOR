from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:  # Optional typing only; no runtime import dependency
    from core.ports.cache import CachePort, StagingPort  # type: ignore
    from core.ports.storage import QueryReadPort, RecorderWritePort  # type: ignore
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


# Re-export tools for backward compatibility (after ToolContext definition to avoid circular imports)
from .bootstrap_tool import bootstrap_story_tool  # noqa: E402
from .indexing_tool import indexing_tool  # noqa: E402
from .narrative_tool import narrative_tool  # noqa: E402
from .notes_tool import notes_tool  # noqa: E402
from .object_tool import object_upload_tool  # noqa: E402
from .query_tool import query_tool, rules_tool  # noqa: E402
from .recorder_tool import recorder_tool  # noqa: E402
from .retrieval_tool import retrieval_tool  # noqa: E402

__all__ = [
    "ToolContext",
    "query_tool",
    "rules_tool",
    "recorder_tool",
    "narrative_tool",
    "indexing_tool",
    "retrieval_tool",
    "object_upload_tool",
    "bootstrap_story_tool",
    "notes_tool",
]
