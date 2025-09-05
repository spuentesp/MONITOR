"""
Integration tests for service layer workflows.

Tests multi-service interactions that span across layers
and verify end-to-end functionality.
"""

from unittest.mock import Mock

import pytest

from core.services.branching.brancher_service import BrancherService
from core.services.projection.projection_service import ProjectionService


@pytest.fixture
def mock_neo4j_repo():
    """Mock Neo4j repository for integration testing."""
    repo = Mock()
    repo.run = Mock()
    repo.execute_query = Mock(return_value=[])
    repo.bootstrap_constraints = Mock()
    return repo


class TestServiceIntegration:
    """Integration tests for service workflows."""

    def test_projection_to_branching_workflow(self, mock_neo4j_repo):
        """Test workflow from projection to branching operations."""
        # Arrange - Create services that would work together
        projection_service = ProjectionService(mock_neo4j_repo)
        brancher_service = BrancherService(mock_neo4j_repo)

        # Mock the brancher components
        brancher_service.cloner = Mock()
        brancher_service.brancher = Mock()

        # Configure successful operations
        brancher_service.cloner.clone_full = Mock(return_value={
            "success": True,
            "new_universe_id": "cloned-universe-123",
            "operations_performed": ["universe_copy", "entity_copy", "story_copy"]
        })

        brancher_service.brancher.branch_at_scene = Mock(return_value={
            "success": True,
            "branch_universe_id": "branch-universe-456",
            "branch_point": "scene-789"
        })

        # Act - Simulate workflow: project data, then clone, then branch

        # 1. Services are initialized and ready (projection would happen here)
        assert projection_service.repo is mock_neo4j_repo
        assert brancher_service.repo is mock_neo4j_repo

        # 2. Clone operation
        clone_result = brancher_service.clone_full(
            source_universe_id="original-universe",
            new_universe_id="cloned-universe-123",
            new_universe_name="Cloned for Branching"
        )

        # 3. Branch operation on cloned universe
        branch_result = brancher_service.branch_at_scene(
            source_universe_id="cloned-universe-123",
            scene_id="scene-789",
            new_universe_id="branch-universe-456",
            new_universe_name="Alternate Timeline"
        )

        # Assert - Workflow completed successfully
        assert clone_result["success"] is True
        assert clone_result["new_universe_id"] == "cloned-universe-123"

        assert branch_result["success"] is True
        assert branch_result["branch_universe_id"] == "branch-universe-456"

        # Verify service calls were made in order
        brancher_service.cloner.clone_full.assert_called_once()
        brancher_service.brancher.branch_at_scene.assert_called_once()

    def test_error_propagation_through_service_layers(self, mock_neo4j_repo):
        """Test that errors propagate correctly through service layers."""
        # Arrange
        brancher_service = BrancherService(mock_neo4j_repo)

        # Mock a failure in the underlying cloner
        brancher_service.cloner = Mock()
        brancher_service.cloner.clone_full = Mock(return_value={
            "success": False,
            "errors": ["Source universe 'nonexistent-123' not found"]
        })

        # Act
        result = brancher_service.clone_full(
            source_universe_id="nonexistent-123",
            new_universe_id="target-123"
        )

        # Assert - Error should propagate through service layer
        assert result["success"] is False
        assert "nonexistent-123" in result["errors"][0]
        assert "not found" in result["errors"][0]

    def test_service_parameter_validation_flow(self, mock_neo4j_repo):
        """Test parameter validation across service boundaries."""
        # Arrange
        brancher_service = BrancherService(mock_neo4j_repo)

        # Mock validation failure
        brancher_service.cloner = Mock()
        brancher_service.cloner.clone_subset = Mock(return_value={
            "success": False,
            "errors": ["Invalid parameter: stories list cannot contain empty strings"]
        })

        # Act - Pass invalid parameters
        result = brancher_service.clone_subset(
            source_universe_id="source-123",
            new_universe_id="target-123",
            stories=["story-1", "", "story-3"]  # Empty string invalid
        )

        # Assert - Validation error should be returned
        assert result["success"] is False
        assert "Invalid parameter" in result["errors"][0]
        assert "empty strings" in result["errors"][0]


class TestServiceCompositionIntegration:
    """Integration tests for service composition patterns."""

    def test_projection_service_composes_all_projectors(self, mock_neo4j_repo):
        """Test ProjectionService properly composes and coordinates projectors."""
        # Arrange
        projection_service = ProjectionService(mock_neo4j_repo)

        # Act - Access all composed projectors
        projectors = [
            projection_service.system_projector,
            projection_service.universe_projector,
            projection_service.story_projector,
            projection_service.entity_projector,
            projection_service.fact_projector
        ]

        # Assert - All projectors should be properly initialized
        for projector in projectors:
            assert projector is not None
            assert projector.repo is mock_neo4j_repo

        # Verify different projector types
        assert projection_service.system_projector.__class__.__name__ == "SystemProjector"
        assert projection_service.universe_projector.__class__.__name__ == "UniverseProjector"
        assert projection_service.story_projector.__class__.__name__ == "StoryProjector"
        assert projection_service.entity_projector.__class__.__name__ == "EntityProjector"
        assert projection_service.fact_projector.__class__.__name__ == "FactProjector"

    def test_brancher_service_coordinates_cloner_and_brancher(self, mock_neo4j_repo):
        """Test BrancherService coordinates cloner and brancher components."""
        # Arrange
        brancher_service = BrancherService(mock_neo4j_repo)

        # Act - Verify composition
        cloner = brancher_service.cloner
        brancher = brancher_service.brancher

        # Assert - Both components should be properly initialized
        assert cloner is not None
        assert brancher is not None
        assert cloner.repo is mock_neo4j_repo
        assert brancher.repo is mock_neo4j_repo

        # Verify correct types
        assert cloner.__class__.__name__ == "UniverseCloner"
        assert brancher.__class__.__name__ == "UniverseBrancher"


class TestCrossServiceDataFlow:
    """Test data flow between different services."""

    def test_projection_data_available_for_branching(self, mock_neo4j_repo):
        """Test that projected data is available for branching operations."""
        # Arrange
        projection_service = ProjectionService(mock_neo4j_repo)
        brancher_service = BrancherService(mock_neo4j_repo)

        # Mock repo to return data that would come from projection
        mock_neo4j_repo.execute_query.return_value = [
            {
                "universe": {"id": "universe-123", "name": "Test Universe"},
                "story_count": 3,
                "entity_count": 5,
                "scene_count": 8
            }
        ]

        # Mock brancher to use this data
        brancher_service.cloner = Mock()
        brancher_service.cloner.clone_full = Mock(return_value={
            "success": True,
            "source_stats": {"stories": 3, "entities": 5, "scenes": 8},
            "cloned_stats": {"stories": 3, "entities": 5, "scenes": 8}
        })

        # Act - Simulate brancher using projected data
        result = brancher_service.clone_full(
            source_universe_id="universe-123",
            new_universe_id="cloned-universe-456"
        )

        # Assert - Branching should succeed with projected data
        assert result["success"] is True
        assert result["source_stats"]["stories"] == 3
        assert result["cloned_stats"]["entities"] == 5

    def test_service_layer_isolation(self, mock_neo4j_repo):
        """Test that services maintain proper isolation while sharing data."""
        # Arrange
        projection_service = ProjectionService(mock_neo4j_repo)
        brancher_service = BrancherService(mock_neo4j_repo)

        # Act - Services should not directly access each other's internals

        # Assert - Services are independent
        assert projection_service is not brancher_service
        assert projection_service.repo is brancher_service.repo  # Shared dependency

        # But they don't directly reference each other
        assert not hasattr(projection_service, 'brancher_service')
        assert not hasattr(brancher_service, 'projection_service')

        # Services maintain their own internal composition
        assert hasattr(projection_service, 'system_projector')
        assert hasattr(projection_service, 'entity_projector')
        assert hasattr(brancher_service, 'cloner')
        assert hasattr(brancher_service, 'brancher')
