"""
Tool context builder using centralized configuration.

Replaces the monolithic build_live_tools function with a clean,
configurable builder following Single Responsibility Principle.
"""

from __future__ import annotations

from collections.abc import Callable
from queue import Queue
from typing import Any

from core.engine.autocommit import AutoCommitWorker
from core.engine.cache import ReadThroughCache, StagingStore
from core.engine.context import (
    AutoCommitContext,
    CacheContext,
    DatabaseContext,
    ServiceContext,
    ToolContext,
)
from core.persistence.neo4j_repo import Neo4jRepo
from core.persistence.queries import QueryService
from core.persistence.recorder import RecorderService

from .service_config import ServiceConfig

# Module-level singletons to avoid spawning a worker per request
_AUTOCOMMIT_WORKER: AutoCommitWorker | None = None
_AUTOCOMMIT_QUEUE: Queue | None = None
_IDEMPOTENCY_SET: set[str] = set()

try:
    from core.engine.cache_redis import RedisReadThroughCache, RedisStagingStore
except ImportError:
    RedisReadThroughCache = None
    RedisStagingStore = None


class ToolContextBuilder:
    """
    Builder for ToolContext using centralized configuration.

    Eliminates scattered configuration logic and provides a clean,
    testable way to build tool contexts with different configurations.
    """

    def __init__(self, config: ServiceConfig | None = None):
        """Initialize builder with optional configuration."""
        self.config = config or ServiceConfig.from_env()

    def build(self, dry_run: bool = True) -> ToolContext:
        """
        Build a configured ToolContext.

        Args:
            dry_run: If True, use mock services instead of live connections

        Returns:
            Fully configured ToolContext
        """
        database_context = self._build_database_context(dry_run)
        cache_context = self._build_cache_context()
        autocommit_context = self._build_autocommit_context(
            database_context.recorder, cache_context.read_cache
        )
        service_context = self._build_service_context()

        return ToolContext(
            database=database_context,
            cache=cache_context,
            autocommit=autocommit_context,
            services=service_context,
        )

    def _build_database_context(self, dry_run: bool) -> DatabaseContext:
        """Build database context with appropriate services."""
        repo = Neo4jRepo().connect()
        recorder = RecorderService(repo)

        if dry_run:
            from ..engine.orchestrator.mock_query_service import MockQueryService

            query_service = MockQueryService()
        else:
            query_service = QueryService(repo)

        return DatabaseContext(
            query_service=query_service,
            recorder=recorder,
            dry_run=dry_run,
        )

    def _build_cache_context(self) -> CacheContext:
        """Build cache context based on configuration."""
        if self.config.cache.cache_type == "redis" and RedisReadThroughCache:
            cache = RedisReadThroughCache(
                url=self.config.cache.redis_url or "redis://localhost:6379"
            )
            staging = RedisStagingStore(url=self.config.cache.redis_url or "redis://localhost:6379")
        else:
            cache = ReadThroughCache()
            staging = StagingStore()

        return CacheContext(
            read_cache=cache,
            staging=staging,
        )

    def _build_autocommit_context(self, recorder: Any, read_cache: Any) -> AutoCommitContext:
        """Build auto-commit context with worker management."""
        global _AUTOCOMMIT_WORKER, _AUTOCOMMIT_QUEUE, _IDEMPOTENCY_SET

        if not self.config.autocommit.enabled:
            return AutoCommitContext(enabled=False)

        # Initialize singleton worker if needed
        if not _AUTOCOMMIT_WORKER:
            _AUTOCOMMIT_QUEUE = Queue()
            _IDEMPOTENCY_SET = set()

            decider = self._create_autocommit_decider()

            _AUTOCOMMIT_WORKER = AutoCommitWorker(
                queue=_AUTOCOMMIT_QUEUE,
                recorder=recorder,
                read_cache=read_cache,
                idempotency=_IDEMPOTENCY_SET,
                decider=decider,
            )
            _AUTOCOMMIT_WORKER.start()

        return AutoCommitContext(
            enabled=True,
            queue=_AUTOCOMMIT_QUEUE,
            worker=_AUTOCOMMIT_WORKER,
            idempotency=_IDEMPOTENCY_SET,
        )

    def _create_autocommit_decider(self) -> Callable[[dict[str, Any]], tuple[bool, str]]:
        """Create auto-commit decision function."""
        if self.config.autocommit.llm_decider_enabled:
            return self._create_llm_decider()
        else:
            return self._create_fallback_decider()

    def _create_llm_decider(self) -> Callable[[dict[str, Any]], tuple[bool, str]]:
        """Create LLM-based auto-commit decider."""

        def _llm_decider(payload: dict[str, Any]) -> tuple[bool, str]:
            try:
                from core.generation.providers import select_llm_from_env

                llm = select_llm_from_env()

                prompt = (
                    "You are AutoCommit. Decide if this change should be committed.\n"
                    'Return ONLY JSON: {"commit": <true|false>, "reason": <short>}\n'
                    f"Payload: {payload}"
                )
                ans = llm.chat([{"role": "user", "content": prompt}])
                txt = ans or "{}"

                import json

                obj = json.loads(txt) if isinstance(txt, str) else {}
                return (bool(obj.get("commit")), str(obj.get("reason") or "agentic"))
            except Exception:
                return False, "decider_llm_error"

        return _llm_decider

    def _create_fallback_decider(self) -> Callable[[dict[str, Any]], tuple[bool, str]]:
        """Create fallback decider when LLM is unavailable."""

        def _no_llm(payload: dict[str, Any]) -> tuple[bool, str]:
            return False, "no_llm_decider"

        return _no_llm

    def _build_service_context(self) -> ServiceContext:
        """Build service context with external services."""
        embedder_fn = self._create_embedder()
        qdrant_index = self._create_qdrant_index()

        return ServiceContext(
            qdrant=qdrant_index,
            embedder=embedder_fn,
        )

    def _create_embedder(self) -> Callable[[str], list[float]]:
        """Create embedding function with fallback."""
        try:
            from sentence_transformers import SentenceTransformer

            embedder = SentenceTransformer(self.config.embedding.model_name)
            return lambda x: embedder.encode(x).tolist()
        except Exception:
            return self._create_fallback_embedder()

    def _create_fallback_embedder(self) -> Callable[[str], list[float]]:
        """Create fallback embedder based on word features."""

        def _fallback_embedder(text: str) -> list[float]:
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
            # Pad/truncate to configured dimension
            while len(features) < self.config.embedding.dimension:
                features.append(0.0)
            return features[: self.config.embedding.dimension]

        return _fallback_embedder

    def _create_qdrant_index(self) -> Any:
        """Create Qdrant index with configuration."""
        try:
            from core.persistence.qdrant_index import QdrantIndex

            return QdrantIndex(
                collection=self.config.qdrant.collection_name,
                dimension=self.config.embedding.dimension,
                host=self.config.qdrant.host,
                port=self.config.qdrant.port,
            )
        except Exception:
            return None
