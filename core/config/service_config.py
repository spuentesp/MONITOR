"""
Centralized service configuration management.

Replaces scattered environment variable parsing with typed configuration classes.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.utils.env import env_bool, env_str


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """Load database config from environment variables."""
        return cls(
            neo4j_uri=env_str("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=env_str("NEO4J_USER", "neo4j"),
            neo4j_password=env_str("NEO4J_PASSWORD", "password"),
        )


@dataclass
class CacheConfig:
    """Cache and staging configuration."""

    cache_type: str = "memory"  # "memory" or "redis"
    redis_url: str | None = None

    @classmethod
    def from_env(cls) -> CacheConfig:
        """Load cache config from environment variables."""
        return cls(
            cache_type=env_str("CACHE_TYPE", "memory"),
            redis_url=env_str("REDIS_URL") if env_str("REDIS_URL") else None,
        )


@dataclass
class AutoCommitConfig:
    """Auto-commit worker configuration."""

    enabled: bool = False
    llm_decider_enabled: bool = False

    @classmethod
    def from_env(cls) -> AutoCommitConfig:
        """Load auto-commit config from environment variables."""
        return cls(
            enabled=env_bool("ENABLE_AUTOCOMMIT"),
            llm_decider_enabled=env_bool("LLM_AUTOCOMMIT_DECIDER"),
        )


@dataclass
class EmbeddingConfig:
    """Embedding model configuration."""

    model_name: str = "all-MiniLM-L6-v2"
    dimension: int = 384

    @classmethod
    def from_env(cls) -> EmbeddingConfig:
        """Load embedding config from environment variables."""
        return cls(
            model_name=env_str("EMBED_MODEL", "all-MiniLM-L6-v2"),
            dimension=int(env_str("EMBED_DIM", "384")),
        )


@dataclass
class QdrantConfig:
    """Qdrant vector database configuration."""

    collection_name: str = "monitor"
    host: str = "localhost"
    port: int = 6333

    @classmethod
    def from_env(cls) -> QdrantConfig:
        """Load Qdrant config from environment variables."""
        return cls(
            collection_name=env_str("QDRANT_COLLECTION", "monitor"),
            host=env_str("QDRANT_HOST", "localhost"),
            port=int(env_str("QDRANT_PORT", "6333")),
        )


@dataclass
class ServiceConfig:
    """
    Complete service configuration container.

    Centralizes all scattered configuration logic from tool_builder
    into a single, typed, testable configuration system.
    """

    database: DatabaseConfig
    cache: CacheConfig
    autocommit: AutoCommitConfig
    embedding: EmbeddingConfig
    qdrant: QdrantConfig

    @classmethod
    def from_env(cls) -> ServiceConfig:
        """Load complete service configuration from environment variables."""
        return cls(
            database=DatabaseConfig.from_env(),
            cache=CacheConfig.from_env(),
            autocommit=AutoCommitConfig.from_env(),
            embedding=EmbeddingConfig.from_env(),
            qdrant=QdrantConfig.from_env(),
        )

    def is_redis_enabled(self) -> bool:
        """Check if Redis caching is enabled and configured."""
        return self.cache.cache_type == "redis" and self.cache.redis_url is not None
