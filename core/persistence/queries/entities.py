from __future__ import annotations

from typing import Any, Protocol

from core.persistence.queries.builders.query_loader import load_query


class QueryExecutor(Protocol):
    """Protocol for executing queries and returning rows."""
    def _rows(self, text: str, **params: Any) -> list[dict[str, Any]]:
        """Execute a query and return rows."""
        ...


class EntitiesQueryService:
    """Service for entity-related queries using composition."""
    
    def __init__(self, query_executor: QueryExecutor):
        self.executor = query_executor
    def entities_in_scene(self, scene_id: str) -> list[dict[str, Any]]:
        return self.executor._rows(
            load_query("entities_in_scene"),
            sid=scene_id,
        )

    def entities_in_story(self, story_id: str) -> list[dict[str, Any]]:
        return self.executor._rows(
            load_query("entities_in_story"),
            sid=story_id,
        )

    def entities_in_universe(self, universe_id: str) -> list[dict[str, Any]]:
        return self.executor._rows(
            load_query("entities_in_universe"),
            uid=universe_id,
        )

    def entities_in_arc(self, arc_id: str) -> list[dict[str, Any]]:
        return self.executor._rows(
            load_query("entities_in_arc"),
            aid=arc_id,
        )

    def entities_in_story_by_role(self, story_id: str, role: str) -> list[dict[str, Any]]:
        return self.executor._rows(
            load_query("entities_in_story_by_role"),
            sid=story_id,
            role=role,
        )

    def entities_in_arc_by_role(self, arc_id: str, role: str) -> list[dict[str, Any]]:
        return self.executor._rows(
            load_query("entities_in_arc_by_role"),
            aid=arc_id,
            role=role,
        )

    def entities_in_universe_by_role(self, universe_id: str, role: str) -> list[dict[str, Any]]:
        return self.executor._rows(
            load_query("entities_in_universe_by_role"),
            uid=universe_id,
            role=role,
        )

    def entity_by_name_in_universe(self, universe_id: str, name: str) -> dict[str, Any] | None:
        rows = self.executor._rows(
            load_query("entity_by_name_in_universe"),
            uid=universe_id,
            name=name,
        )
        return rows[0] if rows else None
