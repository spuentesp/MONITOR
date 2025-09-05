"""Mock query service for dry run and testing scenarios."""

from __future__ import annotations

from typing import Any


class MockQueryService:
    """Mock implementation of QueryService for dry runs and testing.
    
    Returns empty results or placeholder data for all query methods.
    """

    def system_usage_summary(self, *_a, **_k):
        return []

    def effective_system_for_universe(self, *_a, **_k):
        return {}

    def effective_system_for_story(self, *_a, **_k):
        return {}

    def effective_system_for_scene(self, *_a, **_k):
        return {}

    def effective_system_for_entity(self, *_a, **_k):
        return {}

    def effective_system_for_entity_in_story(self, *_a, **_k):
        return {}

    def relation_state_history(self, *_a, **_k):
        return []

    def relations_effective_in_scene(self, *_a, **_k):
        return []

    def relation_is_active_in_scene(self, *_a, **_k):
        return False

    def entities_in_scene(self, *_a, **_k):
        return []

    def entities_in_story(self, *_a, **_k):
        return []

    def entities_in_universe(self, *_a, **_k):
        return []

    def entities_in_universe_by_role(self, *_a, **_k):
        return []

    def participants_by_role_for_scene(self, *_a, **_k):
        return []

    def participants_by_role_for_story(self, *_a, **_k):
        return []

    def facts_for_scene(self, *_a, **_k):
        return []

    def facts_for_story(self, *_a, **_k):
        return []

    def scenes_for_entity(self, *_a, **_k):
        return []

    def scenes_in_story(self, *_a, **_k):
        return []

    def stories_in_universe(self, *_a, **_k):
        return []

    def list_multiverses(self, *_a, **_k):
        return []

    def list_universes_for_multiverse(self, *_a, **_k):
        return []

    def entity_by_name_in_universe(self, *_a, **_k):
        return None

    def commit_deltas(self, **_payload):
        """Mock commit that returns successful result without persistence."""
        return {"ok": True, "written": {}, "warnings": []}
