from __future__ import annotations

from typing import Any, Protocol

from core.persistence.queries.builders.query_loader import load_query


class QueryExecutor(Protocol):
    """Protocol for executing queries and returning rows."""
    def _rows(self, text: str, **params: Any) -> list[dict[str, Any]]:
        """Execute a query and return rows."""
        ...


class RelationsQueryService:
    """Service for relations-related queries using composition."""
    
    def __init__(self, query_executor: QueryExecutor):
        self.executor = query_executor
    def relation_state_history(self, entity_a: str, entity_b: str) -> list[dict[str, Any]]:
        return self.executor._rows(
            load_query("relation_state_history"),
            a=entity_a,
            b=entity_b,
        )

    def relations_effective_in_scene(self, scene_id: str) -> list[dict[str, Any]]:
        return self.executor._rows(
            load_query("relations_effective_in_scene"),
            sid=scene_id,
        )

    def relation_is_active_in_scene(self, entity_a: str, entity_b: str, scene_id: str) -> bool:
        rows = self.executor._rows(
            load_query("relation_is_active_in_scene"),
            a=entity_a,
            b=entity_b,
            sid=scene_id,
        )
        return bool(rows and rows[0].get("active"))
