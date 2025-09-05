"""
Entity repository implementation.

This module provides concrete implementation of entity-specific
persistence operations using the repository pattern.
"""

from typing import Any

from core.interfaces.persistence import EntityRepositoryInterface

from .base_repository import BaseRepository


class EntityRepository(BaseRepository, EntityRepositoryInterface):
    """Concrete implementation of entity repository."""

    def get_entity_type(self) -> str:
        """Return the entity type."""
        return "entity"

    def get_node_label(self, entity_data: dict[str, Any]) -> str:
        """Return the Neo4j label for entities."""
        labels = entity_data.get("labels", ["Entity"])
        return ":".join(labels) if isinstance(labels, list) else "Entity"

    async def create_entity_specific(self, entity_data: dict[str, Any]) -> str:
        """Create a new entity using entity-specific logic."""
        return await self.create_entity(entity_data)

    async def create_entity(self, entity_data: dict[str, Any]) -> str:
        """Create a new entity with validation."""
        label = self.get_node_label(entity_data)
        entity_id, query, params = self._create_basic_entity(entity_data, label)
        return await self._execute_with_fallback(query, params, entity_id)

    async def update_entity_attributes(self, entity_id: str, attributes: dict[str, Any]) -> bool:
        """Update entity attributes."""
        return await self.update(entity_id, attributes)

    async def add_entity_relation(
        self,
        entity_id: str,
        relation_type: str,
        target_id: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Add a relation between entities."""
        try:
            query = (
                """
            MATCH (a {id: $entity_id}), (b {id: $target_id})
            CREATE (a)-[r:`"""
                + relation_type
                + """`]->(b)
            """
            )
            if properties:
                query += "SET r += $properties "
            query += "RETURN r"

            params: dict[str, Any] = {"entity_id": entity_id, "target_id": target_id}
            if properties:
                params["properties"] = properties

            result = await self.neo4j_repo.execute_query(query, params)
            return len(result) > 0
        except Exception:
            return False

    async def remove_entity_relation(
        self, entity_id: str, relation_type: str, target_id: str
    ) -> bool:
        """Remove a relation between entities."""
        try:
            query = (
                """
            MATCH (a {id: $entity_id})-[r:`"""
                + relation_type
                + """`]->(b {id: $target_id})
            DELETE r
            RETURN count(r) as deleted
            """
            )
            result = await self.neo4j_repo.execute_query(
                query, {"entity_id": entity_id, "target_id": target_id}
            )
            return result[0].get("deleted", 0) > 0
        except Exception:
            return False
