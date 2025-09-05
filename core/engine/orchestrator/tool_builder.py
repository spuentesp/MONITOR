"""Tool context building with caching and auto-commit setup."""

from __future__ import annotations

from queue import Queue
from typing import Any

from core.agents.factory import build_agents
from core.engine.autocommit import AutoCommitWorker, DeciderFn
from core.engine.cache import ReadThroughCache, StagingStore
from core.engine.tools import (
    ToolContext,
    bootstrap_story_tool,
    indexing_tool,
    narrative_tool,
    object_upload_tool,
    query_tool,
    recorder_tool,
    retrieval_tool,
)
from core.persistence.neo4j_repo import Neo4jRepo
from core.persistence.queries import QueryService
from core.persistence.recorder import RecorderService
from core.utils.env import env_bool, env_float, env_str

# Module-level singletons to avoid spawning a worker per request
_AUTOCOMMIT_WORKER: AutoCommitWorker | None = None
_AUTOCOMMIT_QUEUE: Queue | None = None
_IDEMPOTENCY_SET: set[str] = set()

try:
    from core.engine.cache_redis import RedisReadThroughCache, RedisStagingStore  # type: ignore
except Exception:  # pragma: no cover
    RedisReadThroughCache = None  # type: ignore
    RedisStagingStore = None  # type: ignore


def _fallback_embedder(text: str) -> list[float]:
    """A dead-simple (word count) embedder when real embedders fail."""
    words = text.split()
    features = [
        len(words),
        len([w for w in words if w.istitle()]),
        len([w for w in words if any(p in w for p in [",", ".", "?", "!"])]),
        len([w for w in words if w.isupper()]),
        len([w for w in words if w.islower()]),
        len([w for w in words if "'" in w]),
        len([w for w in words if w.isdigit()]),
        min(len(words), 7),
    ]
    # Pad/truncate to 384 dimensions (common embedding size)
    while len(features) < 384:
        features.append(0.0)
    return features[:384]


def build_live_tools(dry_run: bool = True) -> ToolContext:
    """Construct a ToolContext backed by the live Neo4j graph using env vars, with optional caching.

    Environment Variables:
    - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`: Neo4j connection
    - `PROVIDER_DEFAULT`: LLM provider selection (openai, anthropic, mock, etc.)
    - `CACHE_TYPE`: 'redis' for RedisReadThroughCache, else in-memory
    - `ENABLE_AUTOCOMMIT`: If 'true', enable auto-commit of staging deltas
    - Various other cache, embedding, and retrieval settings.

    Args:
        dry_run: If True, use a mock query service instead of real Neo4j queries

    Returns:
        Configured ToolContext ready for agent operations
    """
    global _AUTOCOMMIT_WORKER, _AUTOCOMMIT_QUEUE, _IDEMPOTENCY_SET

    repo = Neo4jRepo().connect()
    recorder = RecorderService(repo)

    # Setup query service - mock for dry runs, real for production
    if dry_run:
        from .mock_query_service import MockQueryService
        query_service = MockQueryService()
    else:
        query_service = QueryService(repo)

    # Cache configuration
    cache_type = env_str("CACHE_TYPE", "memory")
    if cache_type == "redis" and RedisReadThroughCache:
        cache = RedisReadThroughCache()
        staging = RedisStagingStore()
    else:
        cache = ReadThroughCache()
        staging = StagingStore()

    # Auto-commit setup
    if env_bool("ENABLE_AUTOCOMMIT") and not _AUTOCOMMIT_WORKER:
        _AUTOCOMMIT_QUEUE = Queue()
        _IDEMPOTENCY_SET = set()

        # Get LLM for agents and decider
        from core.generation.providers import select_llm_from_env
        llm = select_llm_from_env()

        def _llm_decider(payload: dict[str, Any]) -> tuple[bool, str]:
            """LLM-based auto-commit decision function."""
            try:
                prompt = (
                    "You are AutoCommit. Decide if this change should be committed.\n"
                    'Return ONLY JSON: {"commit": <true|false>, "reason": <short>}\n'
                    f"Payload: {payload}"
                )
                ans = llm.chat([{"role": "user", "content": prompt}])
                txt = ans or "{}"
                import json as _json
                obj = _json.loads(txt) if isinstance(txt, str) else {}
                return (bool(obj.get("commit")), str(obj.get("reason") or "agentic"))
            except Exception:
                return False, "decider_llm_error"

        def _no_llm(payload: dict[str, Any]) -> tuple[bool, str]:
            """Fallback decider when LLM is unavailable."""
            return False, "no_llm_decider"

        decider = _llm_decider if env_bool("LLM_AUTOCOMMIT_DECIDER") else _no_llm
        _AUTOCOMMIT_WORKER = AutoCommitWorker(
            queue=_AUTOCOMMIT_QUEUE,
            recorder=recorder,
            read_cache=cache,
            idempotency=_IDEMPOTENCY_SET,
            decider=decider,
        )
        _AUTOCOMMIT_WORKER.start()

    # Embedding configuration
    embed_dim = int(env_str("EMBED_DIM", "384"))
    try:
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer(env_str("EMBED_MODEL", "all-MiniLM-L6-v2"))
        embedder_fn = lambda x: embedder.encode(x).tolist()
    except Exception:
        embedder_fn = _fallback_embedder

    # Index configuration
    try:
        from core.persistence.qdrant_index import QdrantIndex
        index = QdrantIndex(
            collection_name=env_str("QDRANT_COLLECTION", "monitor"),
            dimension=embed_dim,
            host=env_str("QDRANT_HOST", "localhost"),
            port=int(env_str("QDRANT_PORT", "6333")),
        )
    except Exception:
        index = None

    # Build and return tool context
    return ToolContext(
        query_service=query_service,
        recorder=recorder,
        dry_run=dry_run,
        read_cache=cache,
        staging=staging,
        autocommit_enabled=env_bool("ENABLE_AUTOCOMMIT"),
        autocommit_queue=_AUTOCOMMIT_QUEUE,
        autocommit_worker=_AUTOCOMMIT_WORKER,
        idempotency=_IDEMPOTENCY_SET,
        qdrant=index,
        embedder=embedder_fn,
    )
