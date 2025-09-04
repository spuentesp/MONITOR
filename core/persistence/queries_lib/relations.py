from __future__ import annotations

from typing import Any

from core.persistence.queries.builders.query_loader import load_query


class RelationsQueries:
    def relation_state_history(self, entity_a: str, entity_b: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("relation_state_history"),
            a=entity_a,
            b=entity_b,
        )

    def relations_effective_in_scene(self, scene_id: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("relations_effective_in_scene"),
            sid=scene_id,
        )

    def relation_is_active_in_scene(self, entity_a: str, entity_b: str, scene_id: str) -> bool:
        rows = self._rows(
            load_query("relation_is_active_in_scene"),
            a=entity_a,
            b=entity_b,
            sid=scene_id,
        )
        return bool(rows and rows[0].get("active"))
