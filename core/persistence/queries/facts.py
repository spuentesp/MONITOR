from __future__ import annotations

from typing import Any

from core.persistence.queries.builders.query_loader import load_query


class FactsQueries:
    def facts_for_scene(self, scene_id: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("facts_for_scene"),
            sid=scene_id,
        )

    def facts_for_story(self, story_id: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("facts_for_story"),
            sid=story_id,
        )
