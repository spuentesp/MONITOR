"""
Working unit tests for service layer components.

Tests the service components that are actually implemented and importable.
Focuses on composition, initialization, and basic structure rather than
complex business logic that may not be fully implemented.
"""

from unittest.mock import Mock

import pytest

# Test imports that work
from core.services.branching.brancher_service import BrancherService
from core.services.projection.entity_projector import EntityProjector
from core.services.projection.fact_projector import FactProjector
from core.services.projection.projection_service import ProjectionService
from core.services.projection.story_projector import StoryProjector
from core.services.projection.system_projector import SystemProjector
from core.services.projection.universe_projector import UniverseProjector


@pytest.fixture
def mock_repo():
    """Fixture providing mock repository."""
    repo = Mock()
    repo.run = Mock()
    repo.execute_query = Mock()
    repo.bootstrap_constraints = Mock()
    return repo


class TestServiceComposition:
    """Test service composition and initialization."""

    def test_brancher_service_composition(self, mock_repo):
        """Test BrancherService composes cloner and brancher correctly."""
        # Act
        service = BrancherService(mock_repo)

        # Assert
        assert service.repo is mock_repo
        assert hasattr(service, 'cloner')
        assert hasattr(service, 'brancher')
        assert service.cloner.repo is mock_repo
        assert service.brancher.repo is mock_repo

    def test_projection_service_composition(self, mock_repo):
        """Test ProjectionService composes all projectors correctly."""
        # Act
        service = ProjectionService(mock_repo)

        # Assert
        assert service.repo is mock_repo
        assert isinstance(service.system_projector, SystemProjector)
        assert isinstance(service.universe_projector, UniverseProjector)
        assert isinstance(service.story_projector, StoryProjector)
        assert isinstance(service.entity_projector, EntityProjector)
        assert isinstance(service.fact_projector, FactProjector)

        # All projectors should share the same repo
        assert service.system_projector.repo is mock_repo
        assert service.universe_projector.repo is mock_repo
        assert service.story_projector.repo is mock_repo
        assert service.entity_projector.repo is mock_repo
        assert service.fact_projector.repo is mock_repo


class TestProjectorInitialization:
    """Test individual projector initialization."""

    def test_entity_projector_init(self, mock_repo):
        """Test EntityProjector initialization."""
        projector = EntityProjector(mock_repo)
        assert projector.repo is mock_repo

    def test_story_projector_init(self, mock_repo):
        """Test StoryProjector initialization."""
        projector = StoryProjector(mock_repo)
        assert projector.repo is mock_repo

    def test_fact_projector_init(self, mock_repo):
        """Test FactProjector initialization."""
        projector = FactProjector(mock_repo)
        assert projector.repo is mock_repo

    def test_system_projector_init(self, mock_repo):
        """Test SystemProjector initialization."""
        projector = SystemProjector(mock_repo)
        assert projector.repo is mock_repo

    def test_universe_projector_init(self, mock_repo):
        """Test UniverseProjector initialization."""
        projector = UniverseProjector(mock_repo)
        assert projector.repo is mock_repo


class TestServiceMethodSignatures:
    """Test that service methods have expected signatures."""

    def test_brancher_service_methods_exist(self, mock_repo):
        """Test BrancherService has expected methods."""
        service = BrancherService(mock_repo)

        # Check method existence and basic signatures
        assert hasattr(service, 'clone_full')
        assert hasattr(service, 'clone_subset')
        assert hasattr(service, 'branch_at_scene')

        # Verify methods are callable
        assert callable(service.clone_full)
        assert callable(service.clone_subset)
        assert callable(service.branch_at_scene)

    def test_projection_service_methods_exist(self, mock_repo):
        """Test ProjectionService has expected methods."""
        service = ProjectionService(mock_repo)

        # Check main projection method
        assert hasattr(service, 'project_from_yaml')
        assert callable(service.project_from_yaml)

    def test_projector_methods_exist(self, mock_repo):
        """Test individual projectors have expected methods."""
        entity_projector = EntityProjector(mock_repo)
        story_projector = StoryProjector(mock_repo)
        fact_projector = FactProjector(mock_repo)
        system_projector = SystemProjector(mock_repo)
        universe_projector = UniverseProjector(mock_repo)

        # Check entity projector
        assert hasattr(entity_projector, 'project_entities_and_sheets')
        assert callable(entity_projector.project_entities_and_sheets)

        # Check story projector
        assert hasattr(story_projector, 'project_stories_and_scenes')
        assert callable(story_projector.project_stories_and_scenes)

        # Check fact projector
        assert hasattr(fact_projector, 'project_facts_and_relations')
        assert callable(fact_projector.project_facts_and_relations)

        # Check system projector
        assert hasattr(system_projector, 'project_systems')
        assert hasattr(system_projector, 'project_axioms')
        assert hasattr(system_projector, 'project_archetypes')
        assert callable(system_projector.project_systems)
        assert callable(system_projector.project_axioms)
        assert callable(system_projector.project_archetypes)

        # Check universe projector
        assert hasattr(universe_projector, 'project_multiverse')
        assert callable(universe_projector.project_multiverse)


class TestSimpleProjectorOperations:
    """Test basic projector operations that don't require complex domain objects."""

    def test_system_projector_empty_lists(self, mock_repo):
        """Test SystemProjector handles empty lists gracefully."""
        projector = SystemProjector(mock_repo)

        # Act - These should not raise exceptions
        projector.project_systems([])
        projector.project_axioms([])
        projector.project_archetypes([])

        # Assert - Should not call repo for empty lists
        mock_repo.run.assert_not_called()

    def test_system_projector_single_item_lists(self, mock_repo):
        """Test SystemProjector with single item lists."""
        projector = SystemProjector(mock_repo)

        systems = [{"id": "test-system", "name": "Test System", "version": "1.0"}]
        axioms = [{"id": "test-axiom", "name": "Test Axiom", "description": "Test description"}]
        archetypes = [{"id": "test-archetype", "name": "Test Archetype", "description": "Test archetype"}]

        # Act
        projector.project_systems(systems)
        projector.project_axioms(axioms)
        projector.project_archetypes(archetypes)

        # Assert - Should call repo for each item
        assert mock_repo.run.call_count == 3


class TestBrancherServiceDelegation:
    """Test BrancherService properly delegates to component services."""

    def test_clone_operations_delegate_to_cloner(self, mock_repo):
        """Test clone operations delegate to cloner."""
        service = BrancherService(mock_repo)

        # Mock the cloner
        service.cloner = Mock()
        service.cloner.clone_full = Mock(return_value={"success": True})
        service.cloner.clone_subset = Mock(return_value={"success": True})

        # Act
        full_result = service.clone_full("source", "target")
        subset_result = service.clone_subset("source", "target", stories=["story1"])

        # Assert
        assert full_result["success"] is True
        assert subset_result["success"] is True
        service.cloner.clone_full.assert_called_once()
        service.cloner.clone_subset.assert_called_once()

    def test_branch_operations_delegate_to_brancher(self, mock_repo):
        """Test branch operations delegate to brancher."""
        service = BrancherService(mock_repo)

        # Mock the brancher
        service.brancher = Mock()
        service.brancher.branch_at_scene = Mock(return_value={"success": True})

        # Act
        result = service.branch_at_scene("source", "scene", "target")

        # Assert
        assert result["success"] is True
        service.brancher.branch_at_scene.assert_called_once()


class TestServiceErrorHandling:
    """Test basic error handling in services."""

    def test_services_handle_none_repo(self):
        """Test services handle None repository gracefully."""
        # These should not raise exceptions during initialization
        brancher = BrancherService(None)
        projection = ProjectionService(None)

        assert brancher.repo is None
        assert projection.repo is None

    def test_projectors_handle_none_repo(self):
        """Test projectors handle None repository gracefully."""
        # These should not raise exceptions during initialization
        entity_proj = EntityProjector(None)
        story_proj = StoryProjector(None)
        fact_proj = FactProjector(None)
        system_proj = SystemProjector(None)
        universe_proj = UniverseProjector(None)

        assert entity_proj.repo is None
        assert story_proj.repo is None
        assert fact_proj.repo is None
        assert system_proj.repo is None
        assert universe_proj.repo is None
