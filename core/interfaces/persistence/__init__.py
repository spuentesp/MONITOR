"""
Persistence interface contracts.

This package defines the abstract interfaces that must be implemented
by any persistence layer, including read operations, write operations,
and caching.
"""

from .query_interface import QueryInterface, CacheInterface as QueryCacheInterface
from .repository_interface import (
    RepositoryInterface,
    EntityRepositoryInterface,
    FactRepositoryInterface,
    SceneRepositoryInterface,
    SystemRepositoryInterface,
)
from .cache_interface import CacheInterface, DistributedCacheInterface

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
