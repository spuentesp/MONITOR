"""Test branch service functionality."""
import pytest
from unittest.mock import Mock
from core.services.branching import BrancherService


def test_branch_service_creation():
    """Test that BrancherService can be created."""
    mock_repo = Mock()
    service = BrancherService(mock_repo)
    assert service is not None
    assert service.repo is mock_repo
    

def test_branch_service_interface():
    """Test that BrancherService has expected methods."""
    mock_repo = Mock()
    service = BrancherService(mock_repo)
    
    # Check service has the expected interface methods
    assert hasattr(service, 'branch_at_scene')
    assert hasattr(service, 'clone_full')
    assert hasattr(service, 'clone_subset')
    assert callable(getattr(service, 'branch_at_scene'))
    assert callable(getattr(service, 'clone_full'))
    assert callable(getattr(service, 'clone_subset'))


def test_branch_service_composition():
    """Test that BrancherService properly composes its dependencies."""
    mock_repo = Mock()
    service = BrancherService(mock_repo)
    
    # Verify internal composition is set up
    assert service.cloner is not None
    assert service.brancher is not None
    
    # Verify dependencies are properly injected
    assert service.cloner.repo is mock_repo
    assert service.brancher.repo is mock_repo
