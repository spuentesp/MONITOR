"""
Entity domain service.

This module contains business logic for entity operations,
orchestrating between repositories and implementing domain rules.
"""

from typing import Any

from core.interfaces.persistence import EntityRepositoryInterface, QueryInterface


class EntityService:
    """Domain service for entity business logic."""

    def __init__(
        self, entity_repository: EntityRepositoryInterface, query_interface: QueryInterface
    ):
        self.entity_repository = entity_repository
        self.query_interface = query_interface

    async def create_entity_with_validation(self, entity_data: dict[str, Any]) -> dict[str, Any]:
        """Create an entity with business rule validation."""
        # Validate entity data
        validation_result = await self._validate_entity_data(entity_data)
        if not validation_result["valid"]:
            return {"success": False, "errors": validation_result["errors"]}

        # Check for duplicates
        existing = await self._check_for_duplicates(entity_data)
        if existing:
            return {"success": False, "errors": ["Entity with similar attributes already exists"]}

        # Create the entity
        try:
            entity_id = await self.entity_repository.create_entity(entity_data)
            return {"success": True, "entity_id": entity_id}
        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    async def update_entity_with_validation(
        self, entity_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an entity with business rule validation."""
        # Check if entity exists
        entity = await self.query_interface.get_entity_by_id(entity_id)
        if not entity:
            return {"success": False, "errors": ["Entity not found"]}

        # Validate updates
        validation_result = await self._validate_entity_updates(entity, updates)
        if not validation_result["valid"]:
            return {"success": False, "errors": validation_result["errors"]}

        # Apply updates
        try:
            success = await self.entity_repository.update_entity_attributes(entity_id, updates)
            return {"success": success}
        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    async def create_entity_relationship(
        self,
        entity_id: str,
        target_id: str,
        relationship_type: str,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a relationship between entities with validation."""
        # Validate both entities exist
        entity = await self.query_interface.get_entity_by_id(entity_id)
        target = await self.query_interface.get_entity_by_id(target_id)

        if not entity:
            return {"success": False, "errors": ["Source entity not found"]}
        if not target:
            return {"success": False, "errors": ["Target entity not found"]}

        # Validate relationship rules
        validation_result = await self._validate_relationship(entity, target, relationship_type)
        if not validation_result["valid"]:
            return {"success": False, "errors": validation_result["errors"]}

        # Create relationship
        try:
            success = await self.entity_repository.add_entity_relation(
                entity_id, relationship_type, target_id, properties
            )
            return {"success": success}
        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    async def get_entity_with_context(self, entity_id: str) -> dict[str, Any]:
        """Get an entity with its related context (facts, relationships, etc.)."""
        try:
            # Get base entity
            entity = await self.query_interface.get_entity_by_id(entity_id)
            if not entity:
                return {"success": False, "errors": ["Entity not found"]}

            # Get related data
            facts = await self.query_interface.get_facts_for_entity(entity_id)
            relations = await self.query_interface.get_relations_for_entity(entity_id)

            return {
                "success": True,
                "entity": entity,
                "facts": facts,
                "relations": relations,
                "context": {"fact_count": len(facts), "relation_count": len(relations)},
            }
        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    async def search_entities_with_filters(
        self, search_term: str, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search entities with advanced filtering."""
        try:
            # Basic search
            entities = await self.query_interface.search_entities(
                search_term, filters.get("entity_type") if filters else None
            )

            # Apply additional filters
            if filters:
                entities = await self._apply_entity_filters(entities, filters)

            return entities
        except Exception:
            return []

    async def _validate_entity_data(self, entity_data: dict[str, Any]) -> dict[str, Any]:
        """Validate entity data against business rules."""
        errors = []

        # Required fields
        if not entity_data.get("name"):
            errors.append("Entity name is required")

        # Type validation
        entity_type = entity_data.get("type")
        if entity_type and entity_type not in ["character", "location", "item", "concept"]:
            errors.append("Invalid entity type")

        return {"valid": len(errors) == 0, "errors": errors}

    async def _validate_entity_updates(
        self, entity: dict[str, Any], updates: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate entity updates."""
        errors = []

        # Prevent changing critical fields
        if "id" in updates:
            errors.append("Cannot change entity ID")

        # Validate new values
        if "type" in updates and updates["type"] not in [
            "character",
            "location",
            "item",
            "concept",
        ]:
            errors.append("Invalid entity type")

        return {"valid": len(errors) == 0, "errors": errors}

    async def _validate_relationship(
        self, entity: dict[str, Any], target: dict[str, Any], relationship_type: str
    ) -> dict[str, Any]:
        """Validate relationship creation rules."""
        errors = []

        # Same entity check
        if entity.get("id") == target.get("id"):
            errors.append("Cannot create relationship to self")

        # Type-specific rules
        entity_type = entity.get("type")

        if relationship_type == "IS_PARENT_OF" and entity_type != "character":
            errors.append("Only characters can be parents")

        return {"valid": len(errors) == 0, "errors": errors}

    async def _check_for_duplicates(self, entity_data: dict[str, Any]) -> bool:
        """Check if similar entity already exists."""
        try:
            # Simple duplicate check by name and type
            name = entity_data.get("name")
            entity_type = entity_data.get("type")

            if name:
                existing = await self.query_interface.search_entities(name, entity_type)
                return len(existing) > 0
        except Exception:
            pass
        return False

    async def _apply_entity_filters(
        self, entities: list[dict[str, Any]], filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Apply advanced filters to entity list."""
        filtered = entities

        # Filter by minimum fact count
        if "min_facts" in filters:
            min_facts = filters["min_facts"]
            filtered = [e for e in filtered if e.get("fact_count", 0) >= min_facts]

        # Filter by creation date range
        if "created_after" in filters:
            # Implementation would depend on date field structure
            pass

        return filtered
