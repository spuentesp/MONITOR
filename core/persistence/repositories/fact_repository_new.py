"""
Fact repository implementation.

This module provides concrete implementation of fact-specific
persistence operations using the repository pattern.
"""

from typing import Any, Dict, List, Optional
from core.interfaces.persistence import FactRepositoryInterface
from core.domain.base_model import BaseModel


class FactRepository(FactRepositoryInterface):
    """Concrete implementation of fact repository."""
    
    def __init__(self, neo4j_repo, query_service):
        self.neo4j_repo = neo4j_repo
        self.query_service = query_service
    
    async def create(self, entity: BaseModel) -> str:
        """Create a new fact and return its ID."""
        fact_data = entity.model_dump() if hasattr(entity, 'model_dump') else entity.dict()
        entity_id = fact_data.get("entity_id", "")
        if not isinstance(entity_id, str):
            entity_id = ""
        return await self.create_fact(fact_data, entity_id)
    
    async def update(self, entity_id: str, data: Dict[str, Any]) -> bool:
        """Update an existing fact."""
        try:
            query = """
            MATCH (f:Fact {id: $fact_id})
            SET f += $data
            RETURN f
            """
            result = await self.neo4j_repo.execute_query(query, {
                "fact_id": entity_id,
                "data": data
            })
            return len(result) > 0
        except Exception:
            return False
    
    async def delete(self, entity_id: str) -> bool:
        """Delete a fact by ID."""
        try:
            query = """
            MATCH (f:Fact {id: $fact_id})
            DETACH DELETE f
            RETURN count(f) as deleted
            """
            result = await self.neo4j_repo.execute_query(query, {"fact_id": entity_id})
            return result[0].get("deleted", 0) > 0
        except Exception:
            return False
    
    async def save_batch(self, entities: List[BaseModel]) -> List[str]:
        """Save multiple facts in a batch operation."""
        fact_ids = []
        for entity in entities:
            fact_id = await self.create(entity)
            fact_ids.append(fact_id)
        return fact_ids
    
    async def create_fact(self, fact_data: Dict[str, Any], entity_id: str) -> str:
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
            
            params: Dict[str, Any] = {"properties": fact_data}
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
            result = await self.neo4j_repo.execute_query(query, {
                "fact_id": fact_id,
                "entity_id": entity_id
            })
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
            result = await self.neo4j_repo.execute_query(query, {
                "fact_id": fact_id,
                "entity_id": entity_id
            })
            return result[0].get("unlinked", 0) > 0
        except Exception:
            return False
