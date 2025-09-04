"""
Persistence interface contracts.

This package defines the abstract interfaces that must be implemented
by any persistence layer, including read operations, write operations,
and caching.
"""

from .cache_interface import CacheInterface, DistributedCacheInterface
from .query_interface import CacheInterface as QueryCacheInterface
from .query_interface import QueryInterface
from .repository_interface import (
    EntityRepositoryInterface,
    FactRepositoryInterface,
    RepositoryInterface,
    SceneRepositoryInterface,
    SystemRepositoryInterface,
)

__all__ = [
    "QueryInterface",
    "QueryCacheInterface",
    "RepositoryInterface",
    "EntityRepositoryInterface",
    "FactRepositoryInterface",
    "SceneRepositoryInterface",
    "SystemRepositoryInterface",
    "CacheInterface",
    "DistributedCacheInterface",
]
