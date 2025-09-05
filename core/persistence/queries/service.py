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
