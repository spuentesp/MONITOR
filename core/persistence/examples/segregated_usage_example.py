"""
Examples of using segregated interfaces following Interface Segregation Principle.

This demonstrates how clients can depend only on the specific capabilities
they need, rather than being forced to depend on large "fat" interfaces.
"""

from core.interfaces.persistence.segregated_interfaces import (
    CRUDRepositoryInterface,
    EntityRelationshipInterface,
    FactContentInterface,
)
from core.persistence.repositories import (
    EntityRepository,
    FactRepository,
    create_entity_crud_interface,
    create_entity_relationship_interface,
    create_fact_content_interface,
)


class ContentUpdater:
    """
    Client that only needs to update fact content.

    ISP: Depends only on FactContentInterface instead of full FactRepository.
    This makes it clear what this class actually uses and makes testing easier.
    """

    def __init__(self, content_interface: FactContentInterface):
        self._content_interface = content_interface

    async def update_content(self, fact_id: str, new_content: str) -> bool:
        """Update fact content using focused interface."""
        return await self._content_interface.update_fact_content(fact_id, new_content)


class EntityLinker:
    """
    Client that only needs to manage entity relationships.

    ISP: Depends only on EntityRelationshipInterface instead of full EntityRepository.
    """

    def __init__(self, relationship_interface: EntityRelationshipInterface):
        self._relationship_interface = relationship_interface

    async def link_entities(
        self, source_id: str, target_id: str, relation_type: str = "RELATED_TO"
    ) -> bool:
        """Create a relationship between entities."""
        return await self._relationship_interface.add_entity_relation(
            source_id, relation_type, target_id
        )


class BasicCRUDService:
    """
    Service that only needs basic CRUD operations.

    ISP: Depends only on CRUDRepositoryInterface, can work with any repository.
    """

    def __init__(self, crud_interface: CRUDRepositoryInterface):
        self._crud_interface = crud_interface

    async def remove_entity(self, entity_id: str) -> bool:
        """Delete an entity using focused interface."""
        return await self._crud_interface.delete(entity_id)


# Example of how to wire up segregated dependencies
def create_focused_services():
    """
    Demonstrate dependency injection with segregated interfaces.

    Each service gets only the interface it needs, following ISP.
    """
    # Create full repositories (legacy approach)
    entity_repo = EntityRepository(neo4j_repo=None, query_service=None)  # type: ignore
    fact_repo = FactRepository(neo4j_repo=None, query_service=None)  # type: ignore

    # Create segregated interfaces using factory functions
    content_interface = create_fact_content_interface(fact_repo)
    relationship_interface = create_entity_relationship_interface(entity_repo)
    crud_interface = create_entity_crud_interface(entity_repo)

    # Inject focused interfaces into clients
    content_updater = ContentUpdater(content_interface)
    entity_linker = EntityLinker(relationship_interface)
    crud_service = BasicCRUDService(crud_interface)

    return {
        "content_updater": content_updater,
        "entity_linker": entity_linker,
        "crud_service": crud_service,
    }


# Benefits of Interface Segregation:
#
# 1. TESTABILITY: Easy to mock specific interfaces instead of fat repositories
# 2. CLARITY: Classes explicitly declare what they depend on
# 3. FLEXIBILITY: Can swap implementations of specific capabilities
# 4. MAINTAINABILITY: Changes to unused methods don't affect clients
# 5. SINGLE RESPONSIBILITY: Each interface has a focused purpose
