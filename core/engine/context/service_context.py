"""
Service context managing satellite stores and external services.

Handles external service integration responsibilities.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class ServiceContext:
    """Manages satellite stores and external services."""

    # Satellite stores (constructed lazily; connect() when used)
    mongo: Any | None = None
    """MongoStore for document storage."""

    qdrant: Any | None = None
    """QdrantIndex for vector search."""

    opensearch: Any | None = None
    """SearchIndex for full-text search."""

    minio: Any | None = None
    """ObjectStore for file storage."""

    embedder: Callable[[str], list[float]] | None = None
    """Embedding function for text vectorization."""

    rules: Any | None = None
    """Optional rules/system helpers loaded from YAML."""

    def has_vector_search(self) -> bool:
        """Check if vector search is available."""
        return self.qdrant is not None and self.embedder is not None

    def has_text_search(self) -> bool:
        """Check if full-text search is available."""
        return self.opensearch is not None

    def has_document_storage(self) -> bool:
        """Check if document storage is available."""
        return self.mongo is not None

    def has_object_storage(self) -> bool:
        """Check if object storage is available."""
        return self.minio is not None
