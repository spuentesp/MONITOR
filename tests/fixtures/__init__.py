"""
Test fixtures and builders aligned with SOLID architecture.

This package provides reusable test utilities that match our
architectural patterns and enable clean, fast unit testing.
"""

from .context_fixtures import *
from .domain_fixtures import *
from .mock_services import *

__all__ = [
    # Context builders
    "mock_tool_context",
    "mock_database_context", 
    "mock_cache_context",
    "mock_service_context",
    "mock_autocommit_context",
    
    # Domain builders
    "build_test_entity",
    "build_test_fact", 
    "build_test_scene",
    "build_test_universe",
    "build_test_deltas",
    
    # Service mocks
    "MockQueryService",
    "MockNeo4jRepo", 
    "MockCacheService",
    "MockEmbeddingService",
    "MockLLMProvider",
]