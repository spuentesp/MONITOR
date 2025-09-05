"""
System repository implementation.

This module provides concrete implementation of system-specific
persistence operations using the repository pattern.
"""

from typing import Any

from core.interfaces.persistence import SystemRepositoryInterface

from .base_repository import BaseRepository


class SystemRepository(BaseRepository, SystemRepositoryInterface):
    """Concrete implementation of system repository."""

    def get_entity_type(self) -> str:
        """Return the entity type."""
        return "system"

    def get_node_label(self, entity_data: dict[str, Any]) -> str:
        """Return the Neo4j label for systems."""
        return "System"

    async def create_entity_specific(self, entity_data: dict[str, Any]) -> str:
        """Create a new system using system-specific logic."""
        return await self.create_system(entity_data)

    async def create_system(self, system_data: dict[str, Any]) -> str:
        """Create a new system configuration."""
        entity_id, query, params = self._create_basic_entity(system_data)
        return await self._execute_with_fallback(query, params, entity_id)

    async def update_system_rules(self, system_id: str, rules: dict[str, Any]) -> bool:
        """Update system rules and configurations."""
        return await self.update(system_id, {"rules": rules})

    async def apply_system_to_story(self, system_id: str, story_id: str) -> bool:
        """Apply a system to a story."""
        try:
            query = """
            MATCH (sys:System {id: $system_id}), (story:Story {id: $story_id})
            CREATE (story)-[r:USES_SYSTEM]->(sys)
            RETURN r
            """
            result = await self.neo4j_repo.execute_query(
                query, {"system_id": system_id, "story_id": story_id}
            )
            return len(result) > 0
        except Exception:
            return False

    async def remove_system_from_story(self, system_id: str, story_id: str) -> bool:
        """Remove a system from a story."""
        try:
            query = """
            MATCH (story:Story {id: $story_id})-[r:USES_SYSTEM]->(sys:System {id: $system_id})
            DELETE r
            RETURN count(r) as removed
            """
            result = await self.neo4j_repo.execute_query(
                query, {"system_id": system_id, "story_id": story_id}
            )
            return result[0].get("removed", 0) > 0
        except Exception:
            return False
