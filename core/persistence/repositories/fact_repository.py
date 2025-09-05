"""
Fact repository implementation.

This module provides concrete implementation of fact-specific
persistence operations using the repository pattern.
"""

from typing import Any

from core.interfaces.persistence import FactRepositoryInterface

from .base_repository import BaseRepository


class FactRepository(BaseRepository, FactRepositoryInterface):
    """Concrete implementation of fact repository."""

    def get_entity_type(self) -> str:
        """Return the entity type."""
        return "fact"

    def get_node_label(self, entity_data: dict[str, Any]) -> str:
        """Return the Neo4j label for facts."""
        return "Fact"

    async def create_entity_specific(self, entity_data: dict[str, Any]) -> str:
        """Create a new fact using fact-specific logic."""
        entity_id = entity_data.get("entity_id", "")
        if not isinstance(entity_id, str):
            entity_id = ""
        return await self.create_fact(entity_data, entity_id)

    async def create_fact(self, fact_data: dict[str, Any], entity_id: str) -> str:
        """Create a new fact associated with an entity."""
        try:
            # Generate ID if not provided
            fact_id = fact_data.get("id") or f"fact_{hash(str(fact_data)) % 100000}"
            fact_data["id"] = fact_id

            # Create fact node
            query = """
            CREATE (f:Fact $properties)
            """

            # If entity_id provided, link to entity
            if entity_id:
                query += """
                WITH f
                MATCH (e {id: $entity_id})
                CREATE (e)-[:HAS_FACT]->(f)
                """

            query += "RETURN f.id as id"

            params: dict[str, Any] = {"properties": fact_data}
            if entity_id:
                params["entity_id"] = entity_id

            result = await self.neo4j_repo.execute_query(query, params)
            return result[0]["id"] if result else fact_id
        except Exception:
            return fact_data.get("id", f"fact_{hash(str(fact_data)) % 100000}")

    async def update_fact_content(self, fact_id: str, content: str) -> bool:
        """Update the content of a fact."""
        return await self.update(fact_id, {"content": content})

    async def link_fact_to_entity(self, fact_id: str, entity_id: str) -> bool:
        """Link a fact to an entity."""
        try:
            query = """
            MATCH (f:Fact {id: $fact_id}), (e {id: $entity_id})
            CREATE (e)-[:HAS_FACT]->(f)
            RETURN count(f) as linked
            """
            result = await self.neo4j_repo.execute_query(
                query, {"fact_id": fact_id, "entity_id": entity_id}
            )
            return result[0].get("linked", 0) > 0
        except Exception:
            return False

    async def unlink_fact_from_entity(self, fact_id: str, entity_id: str) -> bool:
        """Unlink a fact from an entity."""
        try:
            query = """
            MATCH (e {id: $entity_id})-[r:HAS_FACT]->(f:Fact {id: $fact_id})
            DELETE r
            RETURN count(r) as unlinked
            """
            result = await self.neo4j_repo.execute_query(
                query, {"fact_id": fact_id, "entity_id": entity_id}
            )
            return result[0].get("unlinked", 0) > 0
        except Exception:
            return False
