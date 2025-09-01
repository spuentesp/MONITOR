from __future__ import annotations

from typing import Any

from core.ports.storage import QueryReadPort


class QueryServiceFacade(QueryReadPort):
    """Thin facade that forwards to an underlying QueryService-like object.

    This lets orchestration depend on the port while reusing existing implementation.
    """

    def __init__(self, impl: Any):
        self._impl = impl

    def __getattr__(self, name: str) -> Any:
        # Fallback to underlying implementation for any other methods
        return getattr(self._impl, name)

    # Explicitly expose the commonly used read methods (type-narrowed)
    def entities_in_scene(self, scene_id: str):  # type: ignore[override]
        return self._impl.entities_in_scene(scene_id)

    def entities_in_story(self, story_id: str):  # type: ignore[override]
        return self._impl.entities_in_story(story_id)

    def entities_in_universe(self, universe_id: str):  # type: ignore[override]
        return self._impl.entities_in_universe(universe_id)

    def facts_for_scene(self, scene_id: str):  # type: ignore[override]
        return self._impl.facts_for_scene(scene_id)

    def facts_for_story(self, story_id: str):  # type: ignore[override]
        return self._impl.facts_for_story(story_id)

    def relations_effective_in_scene(self, scene_id: str):  # type: ignore[override]
        return self._impl.relations_effective_in_scene(scene_id)

    # Additional helpers commonly used by Monitor
    def entities_in_universe_by_role(self, universe_id: str, role: str):  # type: ignore[override]
        return self._impl.entities_in_universe_by_role(universe_id, role)

    def participants_by_role_for_scene(self, scene_id: str):  # type: ignore[override]
        return self._impl.participants_by_role_for_scene(scene_id)

    def participants_by_role_for_story(self, story_id: str):  # type: ignore[override]
        return self._impl.participants_by_role_for_story(story_id)

    def scenes_for_entity(self, entity_id: str):  # type: ignore[override]
        return self._impl.scenes_for_entity(entity_id)

    def scenes_in_story(self, story_id: str):  # type: ignore[override]
        return self._impl.scenes_in_story(story_id)

    def stories_in_universe(self, universe_id: str):  # type: ignore[override]
        return self._impl.stories_in_universe(universe_id)

    def list_multiverses(self):  # type: ignore[override]
        return self._impl.list_multiverses()

    def list_universes_for_multiverse(self, multiverse_id: str):  # type: ignore[override]
        return self._impl.list_universes_for_multiverse(multiverse_id)

    def entity_by_name_in_universe(self, universe_id: str, name: str):  # type: ignore[override]
        return self._impl.entity_by_name_in_universe(universe_id, name)
