"""
Segregated interface adapters.

Demonstrates how existing repositories can implement focused segregated
interfaces instead of fat interfaces. This allows clients to depend only
on the specific capabilities they need.
"""

from typing import Any

from core.domain.base_model import BaseModel
from core.interfaces.persistence.segregated_interfaces import (
    BatchOperationsInterface,
    # Core interfaces
    CRUDRepositoryInterface,
    EntityRelationshipInterface,
    FactContentInterface,
    # Fact interfaces
    FactLinkingInterface,
)

from .entity_repository import EntityRepository
from .fact_repository import FactRepository


class EntityCRUDAdapter(CRUDRepositoryInterface):
    """Adapter that exposes only CRUD operations from EntityRepository."""

    def __init__(self, entity_repo: EntityRepository):
        self._repo = entity_repo

    async def create(self, entity: BaseModel) -> str:
        """Create a new entity and return its ID."""
        return await self._repo.create(entity)

    async def update(self, entity_id: str, data: dict[str, Any]) -> bool:
        """Update an existing entity."""
        return await self._repo.update(entity_id, data)

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        return await self._repo.delete(entity_id)


class EntityRelationshipAdapter(EntityRelationshipInterface):
    """Adapter that exposes only relationship operations from EntityRepository."""

    def __init__(self, entity_repo: EntityRepository):
        self._repo = entity_repo

    async def add_entity_relation(
        self,
        entity_id: str,
        relation_type: str,
        target_id: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Add a relation between entities."""
        return await self._repo.add_entity_relation(entity_id, relation_type, target_id, properties)

    async def remove_entity_relation(
        self, entity_id: str, relation_type: str, target_id: str
    ) -> bool:
        """Remove a relation between entities."""
        return await self._repo.remove_entity_relation(entity_id, relation_type, target_id)


class FactContentAdapter(FactContentInterface):
    """Adapter that exposes only content management from FactRepository."""

    def __init__(self, fact_repo: FactRepository):
        self._repo = fact_repo

    async def update_fact_content(self, fact_id: str, content: str) -> bool:
        """Update the content of a fact."""
        return await self._repo.update_fact_content(fact_id, content)


class FactLinkingAdapter(FactLinkingInterface):
    """Adapter that exposes only linking operations from FactRepository."""

    def __init__(self, fact_repo: FactRepository):
        self._repo = fact_repo

    async def link_fact_to_entity(self, fact_id: str, entity_id: str) -> bool:
        """Link a fact to an entity."""
        return await self._repo.link_fact_to_entity(fact_id, entity_id)

    async def unlink_fact_from_entity(self, fact_id: str, entity_id: str) -> bool:
        """Unlink a fact from an entity."""
        return await self._repo.unlink_fact_from_entity(fact_id, entity_id)


class BatchOperationsAdapter(BatchOperationsInterface):
    """Adapter that exposes only batch operations from any BaseRepository."""

    def __init__(self, repo):
        self._repo = repo

    async def save_batch(self, entities: list[BaseModel]) -> list[str]:
        """Save multiple entities in a batch operation."""
        return await self._repo.save_batch(entities)


# Factory functions for creating segregated interfaces
def create_entity_crud_interface(entity_repo: EntityRepository) -> CRUDRepositoryInterface:
    """Create a CRUD-only interface for entity operations."""
    return EntityCRUDAdapter(entity_repo)


def create_entity_relationship_interface(
    entity_repo: EntityRepository,
) -> EntityRelationshipInterface:
    """Create a relationship-only interface for entity operations."""
    return EntityRelationshipAdapter(entity_repo)


def create_fact_content_interface(fact_repo: FactRepository) -> FactContentInterface:
    """Create a content-only interface for fact operations."""
    return FactContentAdapter(fact_repo)


def create_fact_linking_interface(fact_repo: FactRepository) -> FactLinkingInterface:
    """Create a linking-only interface for fact operations."""
    return FactLinkingAdapter(fact_repo)


def create_batch_interface(repo) -> BatchOperationsInterface:
    """Create a batch-only interface for any repository."""
    return BatchOperationsAdapter(repo)
