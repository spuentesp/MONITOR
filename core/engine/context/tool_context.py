"""
Composed ToolContext using focused components.

Replaces the monolithic ToolContext with a composition of specialized contexts,
following the Single Responsibility Principle.
"""

from __future__ import annotations

from dataclasses import dataclass

from .autocommit_context import AutoCommitContext
from .cache_context import CacheContext
from .database_context import DatabaseContext
from .service_context import ServiceContext


@dataclass
class ToolContext:
    """
    Composed tool context with focused responsibilities.

    This class replaces the monolithic ToolContext by composing
    specialized context objects, each handling a single concern.
    """

    database: DatabaseContext
    """Database operations and connections."""

    cache: CacheContext
    """Caching and staging operations."""

    autocommit: AutoCommitContext
    """Auto-commit background operations."""

    services: ServiceContext
    """Satellite stores and external services."""

    # Legacy compatibility properties
    @property
    def query_service(self):
        """Legacy compatibility: access database query service."""
        return self.database.query_service

    @property
    def recorder(self):
        """Legacy compatibility: access database recorder."""
        return self.database.recorder

    @property
    def dry_run(self) -> bool:
        """Legacy compatibility: check if in dry-run mode."""
        return self.database.dry_run

    @property
    def read_cache(self):
        """Legacy compatibility: access read cache."""
        return self.cache.read_cache

    @property
    def staging(self):
        """Legacy compatibility: access staging."""
        return self.cache.staging

    @property
    def autocommit_enabled(self) -> bool:
        """Legacy compatibility: check if auto-commit is enabled."""
        return self.autocommit.enabled

    @property
    def autocommit_queue(self):
        """Legacy compatibility: access auto-commit queue."""
        return self.autocommit.queue

    @property
    def autocommit_worker(self):
        """Legacy compatibility: access auto-commit worker."""
        return self.autocommit.worker

    @property
    def idempotency(self):
        """Legacy compatibility: access idempotency set."""
        return self.autocommit.idempotency

    @property
    def mongo(self):
        """Legacy compatibility: access mongo service."""
        return self.services.mongo

    @property
    def qdrant(self):
        """Legacy compatibility: access qdrant service."""
        return self.services.qdrant

    @property
    def opensearch(self):
        """Legacy compatibility: access opensearch service."""
        return self.services.opensearch

    @property
    def minio(self):
        """Legacy compatibility: access minio service."""
        return self.services.minio

    @property
    def embedder(self):
        """Legacy compatibility: access embedder function."""
        return self.services.embedder

    @property
    def rules(self):
        """Legacy compatibility: access rules."""
        return self.services.rules
