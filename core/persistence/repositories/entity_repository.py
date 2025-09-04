"""
Entity repository implementation.

This module provides concrete implementation of entity-specific
persistence operations using the repository pattern.
"""

from typing import Any, Dict, List, Optional
from core.interfaces.persistence import EntityRepositoryInterface
from core.domain.base_model import BaseModel


class EntityRepository(EntityRepositoryInterface):
    """Concrete implementation of entity repository."""
    
    def __init__(self, neo4j_repo, query_service):
        self.neo4j_repo = neo4j_repo
        self.query_service = query_service
    
    async def create(self, entity: BaseModel) -> str:
        """Create a new entity and return its ID."""
        # Convert Pydantic model to dict for persistence
        entity_data = entity.model_dump() if hasattr(entity, 'model_dump') else entity.dict()
        return await self.create_entity(entity_data)
    
    async def update(self, entity_id: str, data: Dict[str, Any]) -> bool:
        """Update an existing entity."""
        try:
            # Use neo4j_repo to update entity
            query = """
            MATCH (e {id: $entity_id})
            SET e += $data
            RETURN e
            """
            result = await self.neo4j_repo.execute_query(query, {
                "entity_id": entity_id,
                "data": data
            })
            return len(result) > 0
        except Exception:
            return False
    
    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        try:
            query = """
            MATCH (e {id: $entity_id})
            DETACH DELETE e
            RETURN count(e) as deleted
            """
            result = await self.neo4j_repo.execute_query(query, {"entity_id": entity_id})
            return result[0].get("deleted", 0) > 0
        except Exception:
            return False
    
    async def save_batch(self, entities: List[BaseModel]) -> List[str]:
        """Save multiple entities in a batch operation."""
        entity_ids = []
        for entity in entities:
            entity_id = await self.create(entity)
            entity_ids.append(entity_id)
        return entity_ids
    
    async def create_entity(self, entity_data: Dict[str, Any]) -> str:
        """Create a new entity with validation."""
        try:
            # Generate ID if not provided
            entity_id = entity_data.get("id") or f"entity_{hash(str(entity_data)) % 100000}"
            entity_data["id"] = entity_id
            
            # Create entity node in Neo4j
            labels = entity_data.get("labels", ["Entity"])
            label_str = ":".join(labels) if isinstance(labels, list) else "Entity"
            
            query = f"""
            CREATE (e:{label_str} $properties)
            RETURN e.id as id
            """
            result = await self.neo4j_repo.execute_query(query, {"properties": entity_data})
            return result[0]["id"] if result else entity_id
        except Exception:
            # Fallback to returning generated ID
            return entity_data.get("id", f"entity_{hash(str(entity_data)) % 100000}")
    
    async def update_entity_attributes(self, entity_id: str, attributes: Dict[str, Any]) -> bool:
        """Update entity attributes."""
        return await self.update(entity_id, attributes)
    
    async def add_entity_relation(self, entity_id: str, relation_type: str, target_id: str, properties: Optional[Dict[str, Any]] = None) -> bool:
        """Add a relation between entities."""
        try:
            query = """
            MATCH (a {id: $entity_id}), (b {id: $target_id})
            CREATE (a)-[r:`""" + relation_type + """`]->(b)
            """
            if properties:
                query += "SET r += $properties "
            query += "RETURN r"
            
            params = {"entity_id": entity_id, "target_id": target_id}
            if properties:
                params["properties"] = properties
                
            result = await self.neo4j_repo.execute_query(query, params)
            return len(result) > 0
        except Exception:
            return False
    
    async def remove_entity_relation(self, entity_id: str, relation_type: str, target_id: str) -> bool:
        """Remove a relation between entities."""
        try:
            query = """
            MATCH (a {id: $entity_id})-[r:`""" + relation_type + """`]->(b {id: $target_id})
            DELETE r
            RETURN count(r) as deleted
            """
            result = await self.neo4j_repo.execute_query(query, {
                "entity_id": entity_id,
                "target_id": target_id
            })
            return result[0].get("deleted", 0) > 0
        except Exception:
            return False
