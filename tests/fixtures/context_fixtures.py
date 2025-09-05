"""
Context and configuration fixtures for testing.

Provides builders for ToolContext and component contexts
that align with our SOLID architecture.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

from core.engine.context import (
    AutoCommitContext,
    CacheContext, 
    DatabaseContext,
    ServiceContext,
    ToolContext,
)
from .mock_services import (
    MockCacheService,
    MockEmbeddingService,
    MockLLMProvider,
    MockNeo4jRepo,
    MockQueryService,
)


def mock_database_context() -> DatabaseContext:
    """Create a mock DatabaseContext for testing."""
    return DatabaseContext(
        neo4j_repo=MockNeo4jRepo(),
        query_service=MockQueryService(),
        mongo_store=Mock()
    )


def mock_cache_context() -> CacheContext:
    """Create a mock CacheContext for testing."""
    return CacheContext(
        read_cache=MockCacheService(),
        staging=Mock(),
        qdrant_index=Mock()
    )


def mock_service_context() -> ServiceContext:
    """Create a mock ServiceContext for testing.""" 
    return ServiceContext(
        embedder=MockEmbeddingService(),
        providers={"openai": MockLLMProvider()},
        indexer=Mock(),
        retriever=Mock(),
        object_service=Mock()
    )


def mock_autocommit_context() -> AutoCommitContext:
    """Create a mock AutoCommitContext for testing."""
    return AutoCommitContext(
        recorder=Mock(),
        projector=Mock(),
        autocommit_queue=Mock(),
        idempotency_set=set()
    )


def mock_tool_context(
    database: DatabaseContext | None = None,
    cache: CacheContext | None = None, 
    services: ServiceContext | None = None,
    autocommit: AutoCommitContext | None = None,
    dry_run: bool = True
) -> ToolContext:
    """
    Create a mock ToolContext for testing.
    
    Provides defaults for all contexts while allowing selective override.
    """
    return ToolContext(
        database=database or mock_database_context(),
        cache=cache or mock_cache_context(),
        services=services or mock_service_context(),
        autocommit=autocommit or mock_autocommit_context(),
        dry_run=dry_run
    )