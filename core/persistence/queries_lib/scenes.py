from __future__ import annotations

from typing import Any

from core.persistence.query_files.builders.query_loader import load_query


class ScenesQueries:
    def scenes_for_entity(self, entity_id: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("scenes_for_entity"),
            eid=entity_id,
        )

    def participants_by_role_for_scene(self, scene_id: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("participants_by_role_for_scene"),
            sid=scene_id,
        )

    def participants_by_role_for_story(self, story_id: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("participants_by_role_for_story"),
            sid=story_id,
        )

    def next_scene_for_entity_in_story(
        self, story_id: str, entity_id: str, after_sequence_index: int
    ) -> dict[str, Any] | None:
        rows = self._rows(
            load_query("next_scene_for_entity_in_story"),
            sid=story_id,
            eid=entity_id,
            idx=after_sequence_index,
        )
        return rows[0] if rows else None

    def previous_scene_for_entity_in_story(
        self, story_id: str, entity_id: str, before_sequence_index: int
    ) -> dict[str, Any] | None:
        rows = self._rows(
            load_query("previous_scene_for_entity_in_story"),
            sid=story_id,
            eid=entity_id,
            idx=before_sequence_index,
        )
        return rows[0] if rows else None

    def stories_in_universe(self, universe_id: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("stories_in_universe"),
            uid=universe_id,
        )

    def scenes_in_story(self, story_id: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("scenes_in_story"),
            sid=story_id,
        )
