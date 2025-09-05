from __future__ import annotations

from typing import Any, Protocol

from core.persistence.queries.builders.query_loader import load_query


class QueryExecutor(Protocol):
    """Protocol for executing queries and returning rows."""
    def _rows(self, text: str, **params: Any) -> list[dict[str, Any]]:
        """Execute a query and return rows."""
        ...


class FactsQueryService:
    """Service for fact-related queries using composition."""
    
    def __init__(self, query_executor: QueryExecutor):
        self.executor = query_executor
    
    def facts_for_scene(self, scene_id: str) -> list[dict[str, Any]]:
        return self.executor._rows(
            load_query("facts_for_scene"),
            sid=scene_id,
        )

    def facts_for_story(self, story_id: str) -> list[dict[str, Any]]:
        return self.executor._rows(
            load_query("facts_for_story"),
            sid=story_id,
        )
