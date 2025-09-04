"""
Scene repository implementation.

This module provides concrete implementation of scene-specific
persistence operations using the repository pattern.
"""

from typing import Any, Dict, List, Optional
from core.interfaces.persistence import SceneRepositoryInterface
from core.domain.base_model import BaseModel


class SceneRepository(SceneRepositoryInterface):
    """Concrete implementation of scene repository."""
    
    def __init__(self, neo4j_repo, query_service):
        self.neo4j_repo = neo4j_repo
        self.query_service = query_service
    
    async def create(self, entity: BaseModel) -> str:
        """Create a new scene and return its ID."""
        scene_data = entity.model_dump() if hasattr(entity, 'model_dump') else entity.dict()
        return await self.create_scene(scene_data)
    
    async def update(self, scene_id: str, data: Dict[str, Any]) -> bool:
        """Update an existing scene."""
        try:
            query = """
            MATCH (s:Scene {id: $scene_id})
            SET s += $data
            RETURN s
            """
            result = await self.neo4j_repo.execute_query(query, {
                "scene_id": scene_id,
                "data": data
            })
            return len(result) > 0
        except Exception:
            return False
    
    async def delete(self, scene_id: str) -> bool:
        """Delete a scene by ID."""
        try:
            query = """
            MATCH (s:Scene {id: $scene_id})
            DETACH DELETE s
            RETURN count(s) as deleted
            """
            result = await self.neo4j_repo.execute_query(query, {"scene_id": scene_id})
            return result[0].get("deleted", 0) > 0
        except Exception:
            return False
    
    async def save_batch(self, entities: List[BaseModel]) -> List[str]:
        """Save multiple scenes in a batch operation."""
        scene_ids = []
        for entity in entities:
            scene_id = await self.create(entity)
            scene_ids.append(scene_id)
        return scene_ids
    
    async def create_scene(self, scene_data: Dict[str, Any]) -> str:
        """Create a new scene."""
        try:
            # Generate ID if not provided
            scene_id = scene_data.get("id") or f"scene_{hash(str(scene_data)) % 100000}"
            scene_data["id"] = scene_id
            
            # Create scene node
            query = """
            CREATE (s:Scene $properties)
            RETURN s.id as id
            """
            result = await self.neo4j_repo.execute_query(query, {"properties": scene_data})
            return result[0]["id"] if result else scene_id
        except Exception:
            return scene_data.get("id", f"scene_{hash(str(scene_data)) % 100000}")
    
    async def add_participant(self, scene_id: str, entity_id: str, role: str) -> bool:
        """Add a participant to a scene."""
        try:
            query = """
            MATCH (s:Scene {id: $scene_id}), (e {id: $entity_id})
            CREATE (s)-[r:HAS_PARTICIPANT {role: $role}]->(e)
            RETURN r
            """
            result = await self.neo4j_repo.execute_query(query, {
                "scene_id": scene_id,
                "entity_id": entity_id,
                "role": role
            })
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
            result = await self.neo4j_repo.execute_query(query, {
                "scene_id": scene_id,
                "entity_id": entity_id
            })
            return result[0].get("removed", 0) > 0
        except Exception:
            return False
    
    async def update_scene_status(self, scene_id: str, status: str) -> bool:
        """Update the status of a scene."""
        return await self.update(scene_id, {"status": status})
