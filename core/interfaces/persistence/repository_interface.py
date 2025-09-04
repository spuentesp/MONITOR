"""
Repository interface contracts for write operations.

This module defines the abstract interfaces that must be implemented
by any repository providing write operations and domain-specific logic.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from core.domain.base_model import BaseModel


class RepositoryInterface(ABC):
    """Abstract interface for write operations."""

    @abstractmethod
    async def create(self, entity: BaseModel) -> str:
        """Create a new entity and return its ID."""
        pass

    @abstractmethod
    async def update(self, entity_id: str, data: Dict[str, Any]) -> bool:
        """Update an existing entity."""
        pass

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        pass

    @abstractmethod
    async def save_batch(self, entities: List[BaseModel]) -> List[str]:
        """Save multiple entities in a batch operation."""
        pass


class EntityRepositoryInterface(RepositoryInterface):
    """Interface for entity-specific repository operations."""

    @abstractmethod
    async def create_entity(self, entity_data: Dict[str, Any]) -> str:
        """Create a new entity with validation."""
        pass

    @abstractmethod
    async def update_entity_attributes(self, entity_id: str, attributes: Dict[str, Any]) -> bool:
        """Update entity attributes."""
        pass

    @abstractmethod
    async def add_entity_relation(self, entity_id: str, relation_type: str, target_id: str, properties: Optional[Dict[str, Any]] = None) -> bool:
        """Add a relation between entities."""
        pass

    @abstractmethod
    async def remove_entity_relation(self, entity_id: str, relation_type: str, target_id: str) -> bool:
        """Remove a relation between entities."""
        pass


class FactRepositoryInterface(RepositoryInterface):
    """Interface for fact-specific repository operations."""

    @abstractmethod
    async def create_fact(self, fact_data: Dict[str, Any], entity_id: str) -> str:
        """Create a new fact associated with an entity."""
        pass

    @abstractmethod
    async def update_fact_content(self, fact_id: str, content: str) -> bool:
        """Update the content of a fact."""
        pass

    @abstractmethod
    async def link_fact_to_entity(self, fact_id: str, entity_id: str) -> bool:
        """Link a fact to an entity."""
        pass

    @abstractmethod
    async def unlink_fact_from_entity(self, fact_id: str, entity_id: str) -> bool:
        """Unlink a fact from an entity."""
        pass


class SceneRepositoryInterface(RepositoryInterface):
    """Interface for scene-specific repository operations."""

    @abstractmethod
    async def create_scene(self, scene_data: Dict[str, Any]) -> str:
        """Create a new scene."""
        pass

    @abstractmethod
    async def add_participant(self, scene_id: str, entity_id: str, role: str) -> bool:
        """Add a participant to a scene."""
        pass

    @abstractmethod
    async def remove_participant(self, scene_id: str, entity_id: str) -> bool:
        """Remove a participant from a scene."""
        pass

    @abstractmethod
    async def update_scene_status(self, scene_id: str, status: str) -> bool:
        """Update the status of a scene."""
        pass


class SystemRepositoryInterface(RepositoryInterface):
    """Interface for system-specific repository operations."""

    @abstractmethod
    async def create_system(self, system_data: Dict[str, Any]) -> str:
        """Create a new system configuration."""
        pass

    @abstractmethod
    async def update_system_rules(self, system_id: str, rules: Dict[str, Any]) -> bool:
        """Update system rules and configurations."""
        pass

    @abstractmethod
    async def apply_system_to_story(self, system_id: str, story_id: str) -> bool:
        """Apply a system to a story."""
        pass

    @abstractmethod
    async def remove_system_from_story(self, system_id: str, story_id: str) -> bool:
        """Remove a system from a story."""
        pass
