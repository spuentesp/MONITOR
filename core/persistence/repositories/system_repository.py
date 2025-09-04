"""
System repository implementation.

This module provides concrete implementation of system-specific
persistence operations using the repository pattern.
"""

from typing import Any

from core.domain.base_model import BaseModel
from core.interfaces.persistence import SystemRepositoryInterface


class SystemRepository(SystemRepositoryInterface):
    """Concrete implementation of system repository."""

    def __init__(self, neo4j_repo, query_service):
        self.neo4j_repo = neo4j_repo
        self.query_service = query_service

    async def create(self, entity: BaseModel) -> str:
        """Create a new system and return its ID."""
        system_data = entity.model_dump() if hasattr(entity, "model_dump") else entity.dict()
        return await self.create_system(system_data)

    async def update(self, system_id: str, data: dict[str, Any]) -> bool:
        """Update an existing system."""
        try:
            query = """
            MATCH (s:System {id: $system_id})
            SET s += $data
            RETURN s
            """
            result = await self.neo4j_repo.execute_query(
                query, {"system_id": system_id, "data": data}
            )
            return len(result) > 0
        except Exception:
            return False

    async def delete(self, system_id: str) -> bool:
        """Delete a system by ID."""
        try:
            query = """
            MATCH (s:System {id: $system_id})
            DETACH DELETE s
            RETURN count(s) as deleted
            """
            result = await self.neo4j_repo.execute_query(query, {"system_id": system_id})
            return result[0].get("deleted", 0) > 0
        except Exception:
            return False

    async def save_batch(self, entities: list[BaseModel]) -> list[str]:
        """Save multiple systems in a batch operation."""
        system_ids = []
        for entity in entities:
            system_id = await self.create(entity)
            system_ids.append(system_id)
        return system_ids

    async def create_system(self, system_data: dict[str, Any]) -> str:
        """Create a new system configuration."""
        try:
            # Generate ID if not provided
            system_id = system_data.get("id") or f"system_{hash(str(system_data)) % 100000}"
            system_data["id"] = system_id

            # Create system node
            query = """
            CREATE (s:System $properties)
            RETURN s.id as id
            """
            result = await self.neo4j_repo.execute_query(query, {"properties": system_data})
            return result[0]["id"] if result else system_id
        except Exception:
            return system_data.get("id", f"system_{hash(str(system_data)) % 100000}")

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
