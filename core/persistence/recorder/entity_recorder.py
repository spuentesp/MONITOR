"""Entity persistence operations."""

from __future__ import annotations

from typing import Any

from .utils import ensure_id, sanitize_value


class EntityRecorder:
    """Handle entity creation and linking."""

    def __init__(self, repo: Any):
        self.repo = repo

    def create_entities(self, new_entities: list[dict[str, Any]], universe_id: str) -> int:
        """Create entities and link to universe."""
        if not universe_id:
            raise ValueError("universe_id is required to create entities")
            
        erows = []
        for e in new_entities:
            eid = ensure_id("entity", e.get("id"))
            erows.append(
                {
                    "id": eid,
                    "name": e.get("name"),
                    "type": e.get("type"),
                    "universe_id": e.get("universe_id") or universe_id,
                    "attributes": sanitize_value(e.get("attributes") or {}),
                }
            )
        self.repo.run(
            """
            UNWIND $rows AS row
            MERGE (e:Entity {id: row.id})
            SET e.name = row.name,
                e.type = coalesce(row.type, e.type),
                e.universe_id = row.universe_id,
                e.attributes = row.attributes
            WITH e, row
            OPTIONAL MATCH (u:Universe {id: row.universe_id})
            FOREACH (_ IN CASE WHEN u IS NULL THEN [] ELSE [1] END | MERGE (e)-[:BELONGS_TO]->(u))
            """,
            rows=erows,
        )
        return len(erows)
