"""
Persistence interface contracts for read operations.

This module defines the abstract interfaces that must be implemented
by any persistence layer providing read operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class QueryInterface(ABC):
    """Abstract interface for read-only query operations."""

    @abstractmethod
    async def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query with optional parameters and return results."""
        pass

    @abstractmethod
    async def get_entity_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific entity by its ID."""
        pass

    @abstractmethod
    async def get_entities_by_type(self, entity_type: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve entities of a specific type."""
        pass

    @abstractmethod
    async def get_facts_for_entity(self, entity_id: str) -> List[Dict[str, Any]]:
        """Retrieve all facts associated with an entity."""
        pass

    @abstractmethod
    async def get_relations_for_entity(self, entity_id: str) -> List[Dict[str, Any]]:
        """Retrieve all relations for an entity."""
        pass

    @abstractmethod
    async def search_entities(self, search_term: str, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for entities matching a term."""
        pass


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
