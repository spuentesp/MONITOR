"""
Segregated repository interfaces following Interface Segregation Principle.

Splits fat interfaces into focused contracts that clients can implement
only the capabilities they need.
"""

from abc import ABC, abstractmethod
from typing import Any

from core.domain.base_model import BaseModel


# Core CRUD interfaces
class CRUDRepositoryInterface(ABC):
    """Basic CRUD operations interface."""

    @abstractmethod
    async def create(self, entity: BaseModel) -> str:
        """Create a new entity and return its ID."""
        pass

    @abstractmethod
    async def update(self, entity_id: str, data: dict[str, Any]) -> bool:
        """Update an existing entity."""
        pass

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        pass


class BatchOperationsInterface(ABC):
    """Batch operations interface."""

    @abstractmethod
    async def save_batch(self, entities: list[BaseModel]) -> list[str]:
        """Save multiple entities in a batch operation."""
        pass


# Entity-specific interfaces
class EntityCreationInterface(ABC):
    """Entity creation with validation."""

    @abstractmethod
    async def create_entity(self, entity_data: dict[str, Any]) -> str:
        """Create a new entity with validation."""
        pass


class EntityAttributesInterface(ABC):
    """Entity attribute management."""

    @abstractmethod
    async def update_entity_attributes(self, entity_id: str, attributes: dict[str, Any]) -> bool:
        """Update entity attributes."""
        pass


class EntityRelationshipInterface(ABC):
    """Entity relationship management."""

    @abstractmethod
    async def add_entity_relation(
        self,
        entity_id: str,
        relation_type: str,
        target_id: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Add a relation between entities."""
        pass

    @abstractmethod
    async def remove_entity_relation(
        self, entity_id: str, relation_type: str, target_id: str
    ) -> bool:
        """Remove a relation between entities."""
        pass


# Fact-specific interfaces
class FactCreationInterface(ABC):
    """Fact creation operations."""

    @abstractmethod
    async def create_fact(self, fact_data: dict[str, Any], entity_id: str) -> str:
        """Create a new fact associated with an entity."""
        pass


class FactContentInterface(ABC):
    """Fact content management."""

    @abstractmethod
    async def update_fact_content(self, fact_id: str, content: str) -> bool:
        """Update the content of a fact."""
        pass


class FactLinkingInterface(ABC):
    """Fact linking operations."""

    @abstractmethod
    async def link_fact_to_entity(self, fact_id: str, entity_id: str) -> bool:
        """Link a fact to an entity."""
        pass

    @abstractmethod
    async def unlink_fact_from_entity(self, fact_id: str, entity_id: str) -> bool:
        """Unlink a fact from an entity."""
        pass


# Scene-specific interfaces
class SceneCreationInterface(ABC):
    """Scene creation operations."""

    @abstractmethod
    async def create_scene(self, scene_data: dict[str, Any]) -> str:
        """Create a new scene."""
        pass


class SceneParticipantInterface(ABC):
    """Scene participant management."""

    @abstractmethod
    async def add_participant(self, scene_id: str, entity_id: str, role: str) -> bool:
        """Add a participant to a scene."""
        pass

    @abstractmethod
    async def remove_participant(self, scene_id: str, entity_id: str) -> bool:
        """Remove a participant from a scene."""
        pass


class SceneStatusInterface(ABC):
    """Scene status management."""

    @abstractmethod
    async def update_scene_status(self, scene_id: str, status: str) -> bool:
        """Update the status of a scene."""
        pass


# System-specific interfaces
class SystemCreationInterface(ABC):
    """System creation operations."""

    @abstractmethod
    async def create_system(self, system_data: dict[str, Any]) -> str:
        """Create a new system configuration."""
        pass


class SystemRulesInterface(ABC):
    """System rules management."""

    @abstractmethod
    async def update_system_rules(self, system_id: str, rules: dict[str, Any]) -> bool:
        """Update system rules and configurations."""
        pass


class SystemStoryInterface(ABC):
    """System-story relationship management."""

    @abstractmethod
    async def apply_system_to_story(self, system_id: str, story_id: str) -> bool:
        """Apply a system to a story."""
        pass

    @abstractmethod
    async def remove_system_from_story(self, system_id: str, story_id: str) -> bool:
        """Remove a system from a story."""
        pass


# Composed interfaces for backward compatibility
class EntityRepository(
    CRUDRepositoryInterface,
    BatchOperationsInterface,
    EntityCreationInterface,
    EntityAttributesInterface,
    EntityRelationshipInterface,
):
    """Complete entity repository interface."""

    pass


class FactRepository(
    CRUDRepositoryInterface,
    BatchOperationsInterface,
    FactCreationInterface,
    FactContentInterface,
    FactLinkingInterface,
):
    """Complete fact repository interface."""

    pass


class SceneRepository(
    CRUDRepositoryInterface,
    BatchOperationsInterface,
    SceneCreationInterface,
    SceneParticipantInterface,
    SceneStatusInterface,
):
    """Complete scene repository interface."""

    pass


class SystemRepository(
    CRUDRepositoryInterface,
    BatchOperationsInterface,
    SystemCreationInterface,
    SystemRulesInterface,
    SystemStoryInterface,
):
    """Complete system repository interface."""

    pass
