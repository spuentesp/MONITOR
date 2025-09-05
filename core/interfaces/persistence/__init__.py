"""
Persistence interface contracts.

This package defines the abstract interfaces that must be implemented
by any persistence layer, including read operations, write operations,
and caching. Provides both legacy fat interfaces and new segregated
interfaces following the Interface Segregation Principle.
"""

from .cache_interface import CacheInterface, DistributedCacheInterface
from .query_interface import CacheInterface as QueryCacheInterface
from .query_interface import QueryInterface
from .repository_interface import (
    EntityRepositoryInterface,
    FactRepositoryInterface,
    RepositoryInterface,
    SceneRepositoryInterface,
    SystemRepositoryInterface,
)

# New segregated interfaces
from .segregated_interfaces import (
    BatchOperationsInterface,
    # Core interfaces
    CRUDRepositoryInterface,
    EntityAttributesInterface,
    # Entity interfaces
    EntityCreationInterface,
    EntityRelationshipInterface,
    FactContentInterface,
    # Fact interfaces
    FactCreationInterface,
    FactLinkingInterface,
    # Scene interfaces
    SceneCreationInterface,
    SceneParticipantInterface,
    SceneStatusInterface,
    # System interfaces
    SystemCreationInterface,
    SystemRulesInterface,
    SystemStoryInterface,
)

# Import composed interfaces with different names to avoid conflicts
from .segregated_interfaces import (
    EntityRepository as SegregatedEntityRepository,
)
from .segregated_interfaces import (
    FactRepository as SegregatedFactRepository,
)
from .segregated_interfaces import (
    SceneRepository as SegregatedSceneRepository,
)
from .segregated_interfaces import (
    SystemRepository as SegregatedSystemRepository,
)

__all__ = [
    # Query and cache interfaces
    "QueryInterface",
    "QueryCacheInterface",
    "CacheInterface",
    "DistributedCacheInterface",
    # Legacy repository interfaces (deprecated but supported)
    "RepositoryInterface",
    "EntityRepositoryInterface",
    "FactRepositoryInterface",
    "SceneRepositoryInterface",
    "SystemRepositoryInterface",
    # New segregated interfaces (recommended)
    "CRUDRepositoryInterface",
    "BatchOperationsInterface",
    "EntityCreationInterface",
    "EntityAttributesInterface",
    "EntityRelationshipInterface",
    "FactCreationInterface",
    "FactContentInterface",
    "FactLinkingInterface",
    "SceneCreationInterface",
    "SceneParticipantInterface",
    "SceneStatusInterface",
    "SystemCreationInterface",
    "SystemRulesInterface",
    "SystemStoryInterface",
    # Composed segregated interfaces
    "SegregatedEntityRepository",
    "SegregatedFactRepository",
    "SegregatedSceneRepository",
    "SegregatedSystemRepository",
]
