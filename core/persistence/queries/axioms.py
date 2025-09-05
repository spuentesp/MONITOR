from __future__ import annotations

from typing import Any, Protocol

from core.persistence.queries.builders.query_loader import load_query


class QueryExecutor(Protocol):
    """Protocol for executing queries and returning rows."""
    def _rows(self, text: str, **params: Any) -> list[dict[str, Any]]:
        """Execute a query and return rows."""
        ...


class AxiomsQueryService:
    """Service for axioms-related queries using composition."""
    
    def __init__(self, query_executor: QueryExecutor):
        self.executor = query_executor
    def axioms_applying_to_universe(self, universe_id: str) -> list[dict[str, Any]]:
        return self.executor._rows(
            load_query("axioms_applying_to_universe"),
            uid=universe_id,
        )

    def axioms_effective_in_scene(self, scene_id: str) -> list[dict[str, Any]]:
        return self.executor._rows(
            load_query("axioms_effective_in_scene"),
            sid=scene_id,
        )
