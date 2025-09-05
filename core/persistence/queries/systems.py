from __future__ import annotations

from typing import Any, Protocol

from core.persistence.queries.builders.query_loader import load_query


class QueryExecutor(Protocol):
    """Protocol for executing queries and returning rows."""
    def _rows(self, text: str, **params: Any) -> list[dict[str, Any]]:
        """Execute a query and return rows."""
        ...


class SystemsQueryService:
    """Service for systems-related queries using composition."""
    
    def __init__(self, query_executor: QueryExecutor):
        self.executor = query_executor
    def system_usage_summary(self, universe_id: str) -> list[dict[str, Any]]:
        return self.executor._rows(
            load_query("system_usage_summary"),
            uid=universe_id,
        )

    def effective_system_for_universe(self, universe_id: str) -> dict[str, Any] | None:
        rows = self.executor._rows(
            load_query("effective_system_for_universe"),
            uid=universe_id,
        )
        return rows[0] if rows else None

    def effective_system_for_story(self, story_id: str) -> dict[str, Any] | None:
        rows = self.executor._rows(
            load_query("effective_system_for_story"),
            sid=story_id,
        )
        return rows[0] if rows else None

    def effective_system_for_scene(self, scene_id: str) -> dict[str, Any] | None:
        rows = self.executor._rows(
            load_query("effective_system_for_scene"),
            sid=scene_id,
        )
        return rows[0] if rows else None

    def effective_system_for_entity(self, entity_id: str) -> dict[str, Any] | None:
        rows = self.executor._rows(
            load_query("effective_system_for_entity"),
            eid=entity_id,
        )
        return rows[0] if rows else None

    def effective_system_for_entity_in_story(
        self, entity_id: str, story_id: str
    ) -> dict[str, Any] | None:
        rows = self.executor._rows(
            load_query("effective_system_for_entity_in_story"),
            eid=entity_id,
            sid=story_id,
        )
        return rows[0] if rows else None
