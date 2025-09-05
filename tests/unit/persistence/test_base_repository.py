"""
Tests for BaseRepository pattern.

Validates the repository base class that eliminates duplication
and provides common patterns across all repository implementations.
"""

import pytest
from unittest.mock import AsyncMock, Mock

from core.persistence.repositories.base_repository import BaseRepository
from tests.fixtures import MockNeo4jRepo, MockQueryService


class ConcreteRepository(BaseRepository):
    """Concrete implementation for testing."""
    
    def get_entity_type(self) -> str:
        return "test_entity"
    
    def get_node_label(self, entity_data: dict) -> str:
        return "TestEntity"


@pytest.mark.asyncio
class TestBaseRepository:
    """Test BaseRepository functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.neo4j_repo = MockNeo4jRepo()
        self.query_service = MockQueryService()
        self.repository = ConcreteRepository(self.neo4j_repo, self.query_service)
    
    async def test_create_generates_id_and_executes_query(self):
        """Test that create generates ID and executes proper query."""
        entity_data = {"name": "Test Entity", "type": "character"}
        
        result = await self.repository.create(entity_data)
        
        # Should return an ID
        assert isinstance(result, str)
        assert result.startswith("test_entity:")
        
        # Should have executed a query
        assert len(self.neo4j_repo.executed_queries) == 1
        query_call = self.neo4j_repo.executed_queries[0]
        assert "CREATE" in query_call["query"]
        assert "TestEntity" in query_call["query"]
    
    async def test_update_executes_set_query(self):
        """Test update method executes SET query."""
        entity_id = "test:123"
        update_data = {"name": "Updated Name", "description": "New description"}
        
        # Mock successful update
        self.neo4j_repo.set_query_result(
            "MATCH (e {id: $id}) SET e += $properties RETURN e",
            [{"e": {"id": entity_id}}]
        )
        
        result = await self.repository.update(entity_id, update_data)
        
        assert result is True
        assert len(self.neo4j_repo.executed_queries) == 1
        query_call = self.neo4j_repo.executed_queries[0]
        assert "SET e +=" in query_call["query"]
        assert query_call["params"]["id"] == entity_id
        assert query_call["params"]["properties"] == update_data
    
    async def test_delete_executes_delete_query(self):
        """Test delete method executes DELETE query."""
        entity_id = "test:123"
        
        # Mock successful deletion
        self.neo4j_repo.set_query_result(
            "MATCH (e {id: $id}) DELETE e RETURN count(e) as deleted",
            [{"deleted": 1}]
        )
        
        result = await self.repository.delete(entity_id)
        
        assert result is True
        assert len(self.neo4j_repo.executed_queries) == 1
        query_call = self.neo4j_repo.executed_queries[0]
        assert "DELETE e" in query_call["query"]
        assert query_call["params"]["id"] == entity_id
    
    async def test_save_batch_processes_multiple_entities(self):
        """Test batch save processes multiple entities."""
        entities = [
            {"name": "Entity 1", "type": "character"},
            {"name": "Entity 2", "type": "location"}
        ]
        
        # Mock batch create results
        for i in range(len(entities)):
            query = f"CREATE (e:TestEntity $properties) RETURN e.id as id"
            self.neo4j_repo.set_query_result(query, [{"id": f"test_entity:{i}"}])
        
        results = await self.repository.save_batch(entities)
        
        assert len(results) == 2
        assert all(isinstance(result, str) for result in results)
        assert len(self.neo4j_repo.executed_queries) == 2
    
    async def test_execute_with_fallback_handles_errors_gracefully(self):
        """Test error handling with fallback ID generation."""
        query = "INVALID QUERY SYNTAX"
        params = {"id": "test:123"}
        fallback_id = "fallback:456"
        
        # This will use the fallback since query will fail
        result = await self.repository._execute_with_fallback(query, params, fallback_id)
        
        assert result == fallback_id
    
    def test_create_basic_entity_generates_valid_structure(self):
        """Test _create_basic_entity helper method."""
        entity_data = {"name": "Test", "description": "A test entity"}
        label = "TestLabel"
        
        entity_id, query, params = self.repository._create_basic_entity(entity_data, label)
        
        # Should generate a valid ID
        assert isinstance(entity_id, str)
        assert ":" in entity_id
        
        # Should create proper Cypher query
        assert "CREATE" in query
        assert "TestLabel" in query
        assert "$properties" in query
        
        # Should include entity data in params
        assert "properties" in params
        assert params["properties"]["name"] == "Test"
        assert params["properties"]["id"] == entity_id


@pytest.mark.unit
def test_base_repository_abstract_methods_require_implementation():
    """Test that BaseRepository requires concrete implementation."""
    
    # Should not be able to instantiate BaseRepository directly
    with pytest.raises(TypeError):
        BaseRepository(Mock(), Mock())  # type: ignore
    
    # Concrete class must implement required methods
    class IncompleteRepository(BaseRepository):
        pass
    
    with pytest.raises(TypeError):
        IncompleteRepository(Mock(), Mock())  # type: ignore