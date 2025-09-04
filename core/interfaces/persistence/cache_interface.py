"""
Cache interface contracts.

This module defines the abstract interfaces that must be implemented
by any caching layer providing cache operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict


class CacheInterface(ABC):
    """Abstract interface for caching operations."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value in the cache with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove a value from the cache."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        pass

    @abstractmethod
    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Retrieve multiple values from the cache."""
        pass

    @abstractmethod
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Store multiple values in the cache."""
        pass


class DistributedCacheInterface(CacheInterface):
    """Interface for distributed caching with additional features."""

    @abstractmethod
    async def lock(self, key: str, timeout: int = 30) -> bool:
        """Acquire a distributed lock."""
        pass

    @abstractmethod
    async def unlock(self, key: str) -> None:
        """Release a distributed lock."""
        pass

    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> int:
        """Atomically increment a numeric value."""
        pass

    @abstractmethod
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key."""
        pass
