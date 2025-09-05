"""
Repository implementations.

This package contains concrete implementations of the repository
pattern for different domain entities, built on a shared BaseRepository
that eliminates common duplication.
"""

from .base_repository import BaseRepository
from .entity_repository import EntityRepository
from .fact_repository import FactRepository
from .scene_repository import SceneRepository

# Segregated interface adapters (optional for focused dependencies)
from .segregated_adapters import (
    BatchOperationsAdapter,
    EntityCRUDAdapter,
    EntityRelationshipAdapter,
    FactContentAdapter,
    FactLinkingAdapter,
    create_batch_interface,
    create_entity_crud_interface,
    create_entity_relationship_interface,
    create_fact_content_interface,
    create_fact_linking_interface,
)
from .system_repository import SystemRepository

__all__ = [
    # Core repository implementations
    "BaseRepository",
    "EntityRepository",
    "FactRepository",
    "SceneRepository",
    "SystemRepository",
    # Segregated interface adapters
    "EntityCRUDAdapter",
    "EntityRelationshipAdapter",
    "FactContentAdapter",
    "FactLinkingAdapter",
    "BatchOperationsAdapter",
    # Factory functions
    "create_entity_crud_interface",
    "create_entity_relationship_interface",
    "create_fact_content_interface",
    "create_fact_linking_interface",
    "create_batch_interface",
]
