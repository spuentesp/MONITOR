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
