"""
Scene repository implementation.

This module provides concrete implementation of scene-specific
persistence operations using the repository pattern.
"""

from typing import Any

from core.interfaces.persistence import SceneRepositoryInterface

from .base_repository import BaseRepository


class SceneRepository(BaseRepository, SceneRepositoryInterface):
    """Concrete implementation of scene repository."""

    def get_entity_type(self) -> str:
        """Return the entity type."""
        return "scene"

    def get_node_label(self, entity_data: dict[str, Any]) -> str:
        """Return the Neo4j label for scenes."""
        return "Scene"

    async def create_entity_specific(self, entity_data: dict[str, Any]) -> str:
        """Create a new scene using scene-specific logic."""
        return await self.create_scene(entity_data)

    async def create_scene(self, scene_data: dict[str, Any]) -> str:
        """Create a new scene."""
        entity_id, query, params = self._create_basic_entity(scene_data)
        return await self._execute_with_fallback(query, params, entity_id)

    async def add_participant(self, scene_id: str, entity_id: str, role: str) -> bool:
        """Add a participant to a scene."""
        try:
            query = """
            MATCH (s:Scene {id: $scene_id}), (e {id: $entity_id})
            CREATE (s)-[r:HAS_PARTICIPANT {role: $role}]->(e)
            RETURN r
            """
            result = await self.neo4j_repo.execute_query(
                query, {"scene_id": scene_id, "entity_id": entity_id, "role": role}
            )
            return len(result) > 0
        except Exception:
            return False

    async def remove_participant(self, scene_id: str, entity_id: str) -> bool:
        """Remove a participant from a scene."""
        try:
            query = """
            MATCH (s:Scene {id: $scene_id})-[r:HAS_PARTICIPANT]->(e {id: $entity_id})
            DELETE r
            RETURN count(r) as removed
            """
            result = await self.neo4j_repo.execute_query(
                query, {"scene_id": scene_id, "entity_id": entity_id}
            )
            return result[0].get("removed", 0) > 0
        except Exception:
            return False

    async def update_scene_status(self, scene_id: str, status: str) -> bool:
        """Update the status of a scene."""
        return await self.update(scene_id, {"status": status})
