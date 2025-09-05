from __future__ import annotations

from .axioms import AxiomsQueryService
from .base import BaseQueries
from .entities import EntitiesQueryService
from .facts import FactsQueryService
from .relations import RelationsQueryService
from .scenes import ScenesQueryService
from .systems import SystemsQueryService


class QueryService(BaseQueries):
    """Main query service using composition of specialized query services."""
    
    def __init__(self, repo):
        super().__init__(repo)
        
        # Compose specialized query services
        self.entities = EntitiesQueryService(self)
        self.scenes = ScenesQueryService(self)
        self.facts = FactsQueryService(self)
        self.relations = RelationsQueryService(self)
        self.axioms = AxiomsQueryService(self)
        self.systems = SystemsQueryService(self)

    # Delegate methods for backward compatibility
    def entities_in_scene(self, scene_id: str):
        return self.entities.entities_in_scene(scene_id)

    def entities_in_story(self, story_id: str):
        return self.entities.entities_in_story(story_id)

    def entities_in_universe(self, universe_id: str):
        return self.entities.entities_in_universe(universe_id)

    def facts_for_scene(self, scene_id: str):
        return self.facts.facts_for_scene(scene_id)

    def facts_for_story(self, story_id: str):
        return self.facts.facts_for_story(story_id)

    def relations_effective_in_scene(self, scene_id: str):
        return self.relations.relations_effective_in_scene(scene_id)

    def entities_in_universe_by_role(self, universe_id: str, role: str):
        return self.entities.entities_in_universe_by_role(universe_id, role)

    def participants_by_role_for_scene(self, scene_id: str):
        return self.scenes.participants_by_role_for_scene(scene_id)

    def participants_by_role_for_story(self, story_id: str):
        return self.scenes.participants_by_role_for_story(story_id)

    def scenes_for_entity(self, entity_id: str):
        return self.scenes.scenes_for_entity(entity_id)

    def scenes_in_story(self, story_id: str):
        return self.scenes.scenes_in_story(story_id)

    # Relations delegation methods
    def relation_state_history(self, entity_a: str, entity_b: str):
        return self.relations.relation_state_history(entity_a, entity_b)

    def relation_is_active_in_scene(self, entity_a: str, entity_b: str, scene_id: str):
        return self.relations.relation_is_active_in_scene(entity_a, entity_b, scene_id)

    # Axioms delegation methods
    def axioms_applying_to_universe(self, universe_id: str):
        return self.axioms.axioms_applying_to_universe(universe_id)

    def axioms_effective_in_scene(self, scene_id: str):
        return self.axioms.axioms_effective_in_scene(scene_id)

    # Additional entities delegation methods
    def entities_in_arc(self, arc_id: str):
        return self.entities.entities_in_arc(arc_id)

    def entities_in_story_by_role(self, story_id: str, role: str):
        return self.entities.entities_in_story_by_role(story_id, role)

    def entities_in_arc_by_role(self, arc_id: str, role: str):
        return self.entities.entities_in_arc_by_role(arc_id, role)

    # Additional scenes delegation methods
    def next_scene_for_entity_in_story(self, story_id: str, entity_id: str, after_sequence_index: int):
        return self.scenes.next_scene_for_entity_in_story(story_id, entity_id, after_sequence_index)

    def previous_scene_for_entity_in_story(self, story_id: str, entity_id: str, before_sequence_index: int):
        return self.scenes.previous_scene_for_entity_in_story(story_id, entity_id, before_sequence_index)

    # Systems delegation methods
    def system_usage_summary(self, universe_id: str):
        return self.systems.system_usage_summary(universe_id)

    def effective_system_for_universe(self, universe_id: str):
        return self.systems.effective_system_for_universe(universe_id)

    def effective_system_for_story(self, story_id: str):
        return self.systems.effective_system_for_story(story_id)

    def effective_system_for_scene(self, scene_id: str):
        return self.systems.effective_system_for_scene(scene_id)

    def effective_system_for_entity(self, entity_id: str):
        return self.systems.effective_system_for_entity(entity_id)

    def effective_system_for_entity_in_story(self, entity_id: str, story_id: str):
        return self.systems.effective_system_for_entity_in_story(entity_id, story_id)
