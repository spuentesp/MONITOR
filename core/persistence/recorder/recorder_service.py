"""Modular recorder service orchestrating focused persistence operations."""

from __future__ import annotations

from typing import Any

from .entity_recorder import EntityRecorder
from .fact_recorder import FactRecorder
from .multiverse_recorder import MultiverseRecorder
from .relation_recorder import RelationRecorder
from .scene_recorder import SceneRecorder
from .story_recorder import StoryRecorder

try:
    from core.ports.storage import RepoPort
except ImportError:  # pragma: no cover
    RepoPort = None  # type: ignore


class RecorderService:
    """Orchestrate focused persistence operations across domain entities.

    Policy: Pydantic-first. Upstream callers should validate with DTOs before invoking.
    """

    def __init__(self, repo: Any):
        self.repo = repo
        self.multiverse_recorder = MultiverseRecorder(repo)
        self.story_recorder = StoryRecorder(repo)
        self.entity_recorder = EntityRecorder(repo)
        self.scene_recorder = SceneRecorder(repo)
        self.fact_recorder = FactRecorder(repo)
        self.relation_recorder = RelationRecorder(repo)

    def _validate_universe_consistency(
        self,
        new_story: dict[str, Any] | None,
        new_arc: dict[str, Any] | None,
        new_entities: list[dict[str, Any]] | None,
        universe_id: str | None,
    ) -> list[str]:
        """Validate universe_id consistency across operations."""
        warnings: list[str] = []
        
        if (
            new_story
            and universe_id
            and new_story.get("universe_id")
            and new_story.get("universe_id") != universe_id
        ):
            warnings.append(
                f"new_story.universe_id ({new_story.get('universe_id')}) differs from provided universe_id ({universe_id})"
            )
        if (
            new_arc
            and universe_id
            and new_arc.get("universe_id")
            and new_arc.get("universe_id") != universe_id
        ):
            warnings.append(
                f"new_arc.universe_id ({new_arc.get('universe_id')}) differs from provided universe_id ({universe_id})"
            )
        if new_entities and universe_id:
            for e in new_entities:
                if e.get("universe_id") and e.get("universe_id") != universe_id:
                    warnings.append(
                        f"entity {e.get('id') or e.get('name')} universe_id ({e.get('universe_id')}) differs from provided universe_id ({universe_id})"
                    )
        
        return warnings

    def commit_deltas(
        self,
        *,
        scene_id: str | None = None,
        facts: list[dict[str, Any]] | None = None,
        relation_states: list[dict[str, Any]] | None = None,
        relations: list[dict[str, Any]] | None = None,
        universe_id: str | None = None,
        new_multiverse: dict[str, Any] | None = None,
        new_universe: dict[str, Any] | None = None,
        new_arc: dict[str, Any] | None = None,
        new_story: dict[str, Any] | None = None,
        new_scene: dict[str, Any] | None = None,
        new_entities: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Commit all deltas using focused recorder modules."""
        facts = facts or []
        relation_states = relation_states or []
        relations = relations or []
        new_entities = new_entities or []
        
        written = {
            "facts": 0,
            "relation_states": 0,
            "relations": 0,
            "entities": 0,
            "scenes": 0,
            "appears_in": 0,
            "stories": 0,
            "arcs": 0,
            "universes": 0,
            "multiverses": 0,
        }
        
        # Preflight validation
        warnings = self._validate_universe_consistency(
            new_story, new_arc, new_entities, universe_id
        )

        # Multiverse operations
        if new_multiverse:
            self.multiverse_recorder.create_multiverse(new_multiverse)
            written["multiverses"] = 1

        # Universe operations
        if new_universe:
            u_id = self.multiverse_recorder.create_universe(new_universe)
            # Set default universe_id for subsequent operations if not provided
            universe_id = universe_id or u_id
            written["universes"] = 1

        # Arc operations
        if new_arc:
            self.story_recorder.create_arc(new_arc, universe_id)
            written["arcs"] = 1

        # Story operations
        if new_story:
            self.story_recorder.create_story(new_story, universe_id)
            written["stories"] = 1

        # Entity operations
        if new_entities:
            written["entities"] = self.entity_recorder.create_entities(new_entities, universe_id)

        # Scene operations
        if new_scene:
            sc_id, appears_in_count, scene_warnings = self.scene_recorder.create_scene(new_scene)
            warnings.extend(scene_warnings)
            written["scenes"] = 1
            written["appears_in"] = appears_in_count
            # Set scene_id for subsequent facts/relation_states defaulting
            scene_id = scene_id or sc_id

        # Fact operations
        if facts:
            written["facts"] = self.fact_recorder.create_facts(facts, scene_id, universe_id)

        # Relation state operations
        if relation_states:
            rs_count, rs_warnings = self.relation_recorder.create_relation_states(
                relation_states, scene_id
            )
            written["relation_states"] = rs_count
            warnings.extend(rs_warnings)

        # Simple relation operations
        if relations:
            written["relations"] = self.relation_recorder.create_simple_relations(relations)

        return {"ok": True, "written": written, "warnings": warnings}
