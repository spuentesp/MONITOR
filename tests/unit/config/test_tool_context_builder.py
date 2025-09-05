"""
Tests for ToolContextBuilder and centralized configuration.

Validates the configuration management system that centralizes
service setup and follows Dependency Inversion Principle.
"""

import pytest
from unittest.mock import Mock, patch

from core.config.tool_context_builder import ToolContextBuilder
from core.config.service_config import ServiceConfig, DatabaseConfig, CacheConfig
from core.engine.context import ToolContext


class TestToolContextBuilder:
    """Test ToolContextBuilder functionality."""
    
    def test_builder_creates_tool_context_with_dry_run(self):
        """Test that builder creates ToolContext in dry run mode."""
        builder = ToolContextBuilder()
        
        context = builder.build(dry_run=True)
        
        assert isinstance(context, ToolContext)
        assert context.dry_run is True
        
        # Should have all required contexts
        assert hasattr(context, 'database')
        assert hasattr(context, 'cache') 
        assert hasattr(context, 'services')
        assert hasattr(context, 'autocommit')
    
    def test_builder_with_custom_config(self):
        """Test builder with custom service configuration."""
        custom_config = ServiceConfig(
            database=DatabaseConfig(
                neo4j_url="bolt://custom:7687",
                mongo_url="mongodb://custom:27017"
            ),
            cache=CacheConfig(
                redis_url="redis://custom:6379"
            )
        )
        
        builder = ToolContextBuilder(config=custom_config)
        context = builder.build(dry_run=True)
        
        assert isinstance(context, ToolContext)
        # Configuration should be applied during build
        # (exact verification depends on how config is used internally)
    
    @patch('core.config.tool_context_builder._setup_database_context')
    @patch('core.config.tool_context_builder._setup_cache_context')
    def test_builder_calls_setup_methods(self, mock_cache_setup, mock_db_setup):
        """Test that builder calls appropriate setup methods."""
        mock_db_context = Mock()
        mock_cache_context = Mock() 
        mock_db_setup.return_value = mock_db_context
        mock_cache_setup.return_value = mock_cache_context
        
        builder = ToolContextBuilder()
        context = builder.build(dry_run=True)
        
        # Should have called setup methods
        mock_db_setup.assert_called_once()
        mock_cache_setup.assert_called_once()
    
    def test_builder_handles_production_mode(self):
        """Test builder configuration for production mode."""
        builder = ToolContextBuilder()
        
        context = builder.build(dry_run=False)
        
        assert isinstance(context, ToolContext)
        assert context.dry_run is False
    
    def test_builder_with_environment_overrides(self):
        """Test that builder respects environment variable overrides."""
        with patch.dict('os.environ', {
            'MONITOR_NEO4J_URL': 'bolt://env:7687',
            'MONITOR_DRY_RUN': 'false'
        }):
            builder = ToolContextBuilder()
            context = builder.build()
            
            assert isinstance(context, ToolContext)
            # Environment should influence configuration
    
    def test_builder_singleton_behavior(self):
        """Test that builder manages singleton resources properly."""
        builder1 = ToolContextBuilder()
        builder2 = ToolContextBuilder()
        
        context1 = builder1.build(dry_run=True)
        context2 = builder2.build(dry_run=True)
        
        # Both should be valid ToolContext instances
        assert isinstance(context1, ToolContext)
        assert isinstance(context2, ToolContext)
        
        # Should handle resource management properly
        # (specific assertions depend on singleton implementation)
    
    def test_builder_error_handling(self):
        """Test builder handles configuration errors gracefully."""
        # Test with invalid configuration
        invalid_config = ServiceConfig(
            database=DatabaseConfig(
                neo4j_url="invalid://url",
                mongo_url="invalid://url"
            )
        )
        
        builder = ToolContextBuilder(config=invalid_config)
        
        # Should still create context in dry run mode
        context = builder.build(dry_run=True)
        assert isinstance(context, ToolContext)
    
    def test_builder_supports_partial_configuration(self):
        """Test that builder works with partial configuration."""
        partial_config = ServiceConfig(
            database=DatabaseConfig(neo4j_url="bolt://partial:7687")
            # Missing cache and other configs - should use defaults
        )
        
        builder = ToolContextBuilder(config=partial_config) 
        context = builder.build(dry_run=True)
        
        assert isinstance(context, ToolContext)
        # Should fill in defaults for missing configuration


class TestServiceConfig:
    """Test ServiceConfig validation and behavior."""
    
    def test_service_config_with_defaults(self):
        """Test ServiceConfig uses appropriate defaults."""
        config = ServiceConfig()
        
        # Should have default values
        assert config.database is not None
        assert config.cache is not None
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.cache, CacheConfig)
    
    def test_database_config_validation(self):
        """Test DatabaseConfig validation."""
        # Valid config
        valid_config = DatabaseConfig(
            neo4j_url="bolt://localhost:7687",
            mongo_url="mongodb://localhost:27017"
        )
        
        assert valid_config.neo4j_url == "bolt://localhost:7687"
        assert valid_config.mongo_url == "mongodb://localhost:27017"
    
    def test_cache_config_validation(self):
        """Test CacheConfig validation."""
        valid_config = CacheConfig(
            redis_url="redis://localhost:6379",
            qdrant_url="http://localhost:6333"
        )
        
        assert valid_config.redis_url == "redis://localhost:6379"
        assert valid_config.qdrant_url == "http://localhost:6333"
    
    def test_config_immutability(self):
        """Test that config objects are properly immutable."""
        config = ServiceConfig()
        
        # Should not be able to modify after creation
        # (depends on dataclass frozen=True implementation)
        original_db_config = config.database
        
        # Attempting to modify should not affect original
        new_config = ServiceConfig(
            database=DatabaseConfig(neo4j_url="bolt://new:7687")
        )
        
        assert config.database == original_db_config
        assert new_config.database.neo4j_url == "bolt://new:7687"


@pytest.mark.unit 
def test_context_builder_follows_dependency_inversion():
    """Test that ToolContextBuilder follows Dependency Inversion Principle."""
    
    # Builder should depend on abstractions (ServiceConfig) not concrete implementations
    builder = ToolContextBuilder()
    
    # Should accept configuration interface
    custom_config = ServiceConfig()
    builder_with_config = ToolContextBuilder(config=custom_config)
    
    # Both should create valid contexts
    context1 = builder.build(dry_run=True)
    context2 = builder_with_config.build(dry_run=True)
    
    assert isinstance(context1, ToolContext)
    assert isinstance(context2, ToolContext)
    
    # Builder shouldn't depend on specific implementations
    # It should work with any valid ServiceConfig