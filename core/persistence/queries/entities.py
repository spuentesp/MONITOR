from __future__ import annotations

from typing import Any

from core.persistence.queries.builders.query_loader import load_query


class EntitiesQueries:
    def entities_in_scene(self, scene_id: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("entities_in_scene"),
            sid=scene_id,
        )

    def entities_in_story(self, story_id: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("entities_in_story"),
            sid=story_id,
        )

    def entities_in_universe(self, universe_id: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("entities_in_universe"),
            uid=universe_id,
        )

    def entities_in_arc(self, arc_id: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("entities_in_arc"),
            aid=arc_id,
        )

    def entities_in_story_by_role(self, story_id: str, role: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("entities_in_story_by_role"),
            sid=story_id,
            role=role,
        )

    def entities_in_arc_by_role(self, arc_id: str, role: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("entities_in_arc_by_role"),
            aid=arc_id,
            role=role,
        )

    def entities_in_universe_by_role(self, universe_id: str, role: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("entities_in_universe_by_role"),
            uid=universe_id,
            role=role,
        )

    def entity_by_name_in_universe(self, universe_id: str, name: str) -> dict[str, Any] | None:
        rows = self._rows(
            load_query("entity_by_name_in_universe"),
            uid=universe_id,
            name=name,
        )
        return rows[0] if rows else None
