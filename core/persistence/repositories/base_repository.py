"""
Base repository implementation providing common patterns.

This module provides a base class that eliminates duplication across
all repository implementations by extracting shared patterns for
CRUD operations, error handling, and ID generation.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any

from core.domain.base_model import BaseModel

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """
    Base repository class providing common patterns for all repositories.

    Eliminates duplication by providing shared implementations for:
    - Constructor pattern (neo4j_repo, query_service injection)
    - Error handling patterns
    - ID generation logic
    - Batch operations
    - Common CRUD operations
    """

    def __init__(self, neo4j_repo, query_service):
        """Initialize repository with injected dependencies."""
        self.neo4j_repo = neo4j_repo
        self.query_service = query_service

    # Abstract methods that subclasses must implement
    @abstractmethod
    async def create_entity_specific(self, entity_data: dict[str, Any]) -> str:
        """Create entity using subclass-specific logic."""
        pass

    @abstractmethod
    def get_entity_type(self) -> str:
        """Return the entity type (e.g., 'fact', 'entity', 'scene')."""
        pass

    @abstractmethod
    def get_node_label(self, entity_data: dict[str, Any]) -> str:
        """Return the Neo4j label for this entity type."""
        pass

    # Common implementations
    async def create(self, entity: BaseModel) -> str:
        """Create a new entity and return its ID."""
        entity_data = self._convert_entity_to_dict(entity)
        return await self.create_entity_specific(entity_data)

    async def update(self, entity_id: str, data: dict[str, Any]) -> bool:
        """Update an existing entity."""
        try:
            label = self.get_node_label({})  # Default label
            query = f"""
            MATCH (e:{label} {{id: $entity_id}})
            SET e += $data
            RETURN e
            """
            result = await self._execute_query(query, {"entity_id": entity_id, "data": data})
            return len(result) > 0
        except Exception as e:
            logger.error(f"Failed to update {self.get_entity_type()} {entity_id}: {e}")
            return False

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        try:
            label = self.get_node_label({})  # Default label
            query = f"""
            MATCH (e:{label} {{id: $entity_id}})
            DETACH DELETE e
            RETURN count(e) as deleted
            """
            result = await self._execute_query(query, {"entity_id": entity_id})
            return result[0].get("deleted", 0) > 0
        except Exception as e:
            logger.error(f"Failed to delete {self.get_entity_type()} {entity_id}: {e}")
            return False

    async def save_batch(self, entities: list[BaseModel]) -> list[str]:
        """Save multiple entities in a batch operation."""
        entity_ids = []
        for entity in entities:
            entity_id = await self.create(entity)
            entity_ids.append(entity_id)
        return entity_ids

    # Protected helper methods
    def _convert_entity_to_dict(self, entity: BaseModel) -> dict[str, Any]:
        """Convert Pydantic model to dict for persistence."""
        return entity.model_dump() if hasattr(entity, "model_dump") else entity.dict()

    def _generate_id(self, prefix: str, data: dict[str, Any]) -> str:
        """Generate ID using consistent pattern."""
        existing_id = data.get("id")
        if existing_id:
            return existing_id
        return f"{prefix}_{hash(str(data)) % 100000}"

    async def _execute_query(self, query: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute query with consistent error handling."""
        try:
            result = await self.neo4j_repo.execute_query(query, params)
            return result if result else []
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            raise

    def _create_basic_entity(
        self, entity_data: dict[str, Any], label: str | None = None
    ) -> tuple[str, str, dict[str, Any]]:
        """
        Prepare basic entity creation data.

        Returns:
            Tuple of (entity_id, cypher_query, query_params)
        """
        # Generate ID if not provided
        entity_type = self.get_entity_type()
        entity_id = self._generate_id(entity_type, entity_data)
        entity_data["id"] = entity_id

        # Determine label
        if label is None:
            label = self.get_node_label(entity_data)

        # Prepare query
        query = f"""
        CREATE (e:{label} $properties)
        RETURN e.id as id
        """
        params = {"properties": entity_data}

        return entity_id, query, params

    async def _execute_with_fallback(
        self, query: str, params: dict[str, Any], fallback_id: str
    ) -> str:
        """Execute query with fallback to generated ID on failure."""
        try:
            result = await self._execute_query(query, params)
            return result[0]["id"] if result else fallback_id
        except Exception as e:
            logger.error(f"Query failed, using fallback ID: {e}")
            return fallback_id
