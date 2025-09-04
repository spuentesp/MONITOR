"""
Enhanced agent tooling for comprehensive narrative context integration.

Combines graph ontology data with narrative content to provide complete story context.
"""

from __future__ import annotations

from typing import Any

from core.domain.narrative_content import (
    CharacterMemory,
    ChatLog,
    EntityDescription,
    GMNote,
    NarrativeState,
    SceneAbstract,
)
from core.services.narrative_content_service import NarrativeContentService


class NarrativeContextProvider:
    """Provides comprehensive context to agents from both graph and narrative content."""
    
    def __init__(self, content_service: NarrativeContentService, query_service: Any = None):
        self.content_service = content_service
        self.query_service = query_service  # Access to graph queries
    
    def get_comprehensive_context(self, universe_id: str, scene_id: str | None = None) -> dict[str, Any]:
        """Get complete narrative and graph context using existing QueryService methods."""
        context = {
            # Use actual QueryService methods (not theoretical ones)
            "stories": self._get_stories_in_universe(universe_id),
            "entities": self._get_entities_in_universe(universe_id),
            
            # Narrative content from MongoDB
            "narrative_state": self.content_service.get_narrative_state(universe_id),
            "gm_notes": self.content_service.get_active_gm_notes(universe_id),
            "content_summary": self.content_service.get_content_stats(universe_id),
        }
        
        if scene_id:
            context.update({
                "current_scene": self._get_scene_context_with_graph(scene_id, universe_id),
                "scene_relationships": self._get_scene_relationships(scene_id),
            })
        
        return context

    def get_story_timeline(self, universe_id: str, story_id: str | None = None) -> dict[str, Any]:
        """Get chronological story progression using actual QueryService methods."""
        timeline = {
            "story_progression": [],
            "key_events": [],
            "character_developments": [],
            "plot_threads": [],
            "unresolved_elements": []
        }
        
        # Use actual QueryService methods
        if self.query_service and story_id:
            try:
                # Get scenes in story (this method actually exists)
                scenes = self.query_service.scenes_in_story(story_id)
                for scene in scenes:
                    scene_context = self._get_scene_context_with_graph(scene.get("id"), universe_id)
                    if scene_context:
                        timeline["story_progression"].append({
                            "scene_id": scene.get("id"),
                            "when": scene.get("when"),
                            "location": scene.get("location"),
                            "participants": scene.get("participants", []),
                            "summary": scene_context.get("abstract"),
                            "narrative_content": scene_context.get("chat_logs", [])[-3:]
                        })
                
                # Get facts for story (this method actually exists)
                facts = self.query_service.facts_for_story(story_id)
                for fact in facts:
                    timeline["key_events"].append({
                        "fact_type": fact.get("fact_type"),
                        "content": fact.get("content"),
                        "when": fact.get("when"),
                        "entities_involved": fact.get("subject_ids", [])
                    })
                    
            except Exception:
                pass  # Graceful degradation if queries fail
        
        # Enhance with narrative content
        narrative_state = self.content_service.get_narrative_state(universe_id)
        if narrative_state:
            timeline["plot_threads"] = narrative_state.active_plot_threads or []
            timeline["unresolved_elements"] = narrative_state.unresolved_questions or []
        
        return timeline

    def get_character_full_context(self, character_id: str, universe_id: str) -> dict[str, Any]:
        """Get complete character context using existing QueryService methods."""
        context = {
            # Use actual QueryService methods
            "entity_data": self._get_entity_from_universe(character_id, universe_id),
            "scene_history": self._get_character_scenes(character_id),
            
            # Narrative content from MongoDB
            "description": self.content_service.get_entity_description(character_id),
            "memory": self.content_service.get_character_memory(character_id),
            "related_notes": self.content_service.get_active_gm_notes(
                universe_id, tags=[f"character:{character_id}"]
            ),
        }
        
        return context

    # Helper methods using ACTUAL QueryService interface
    def _get_stories_in_universe(self, universe_id: str) -> list[dict[str, Any]]:
        """Get stories using actual QueryService method."""
        if not self.query_service:
            return []
        
        try:
            # This method actually exists in QueryService
            return self.query_service.stories_in_universe(universe_id)
        except Exception:
            return []

    def _get_entities_in_universe(self, universe_id: str) -> list[dict[str, Any]]:
        """Get entities using actual QueryService method."""
        if not self.query_service:
            return []
        
        try:
            # This method actually exists in QueryService
            return self.query_service.entities_in_universe(universe_id)
        except Exception:
            return []

    def _get_scene_relationships(self, scene_id: str) -> list[dict[str, Any]]:
        """Get relationships using actual QueryService method."""
        if not self.query_service:
            return []
        
        try:
            # This method actually exists in QueryService
            return self.query_service.relations_effective_in_scene(scene_id)
        except Exception:
            return []

    def _get_entity_from_universe(self, entity_id: str, universe_id: str) -> dict[str, Any]:
        """Get specific entity from universe entities."""
        entities = self._get_entities_in_universe(universe_id)
        for entity in entities:
            if entity.get("id") == entity_id:
                return entity
        return {}

    def _get_character_scenes(self, character_id: str) -> list[dict[str, Any]]:
        """Get scenes for character using actual QueryService method."""
        if not self.query_service:
            return []
        
        try:
            # This method actually exists in QueryService
            return self.query_service.scenes_for_entity(character_id)
        except Exception:
            return []

    def _get_scene_context_with_graph(self, scene_id: str, universe_id: str) -> dict[str, Any]:
        """Get scene context combining QueryService and MongoDB data."""
        context = {}
        
        # Get relationships from QueryService (actual method)
        if self.query_service:
            try:
                relationships = self.query_service.relations_effective_in_scene(scene_id)
                context["relationships"] = relationships
            except Exception:
                context["relationships"] = []
        
        # Get narrative content from MongoDB
        context.update({
            "chat_logs": self.content_service.get_scene_chat_logs(scene_id),
            "abstract": self.content_service.get_scene_abstract(scene_id),
        })
        
        return context

    def _get_character_dialogue_history(self, character_id: str, universe_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent dialogue for character."""
        try:
            # Search for chat logs where this character was the speaker
            # Note: This would need to be implemented in the content service
            # For now, return empty list as placeholder
            return []
        except Exception:
            return []
    
    def get_narrator_context(self, universe_id: str, scene_id: str | None = None) -> dict[str, Any]:
        """Get context specifically useful for the Narrator agent."""
        context = {
            "narrative_state": self.content_service.get_narrative_state(universe_id),
            "gm_notes": self.content_service.get_active_gm_notes(universe_id),
            "content_stats": self.content_service.get_content_stats(universe_id),
        }
        
        if scene_id:
            context.update(self.get_narrator_context(universe_id, scene_id))
        
        return context


class NarrativeContentRecorder:
    """Records agent outputs as narrative content."""
    
    def __init__(self, content_service: NarrativeContentService):
        self.content_service = content_service
    
    def record_chat_message(
        self,
        scene_id: str,
        universe_id: str,
        speaker_id: str | None,
        speaker_name: str,
        message: str,
        message_type: str = "dialogue",
        created_by: str | None = None
    ) -> str:
        """Record a chat message in a scene."""
        chat_log = ChatLog(
            universe_id=universe_id,
            linked_scene_id=scene_id,
            speaker_id=speaker_id,
            speaker_name=speaker_name,
            content=message,
            message_type=message_type,
            created_by=created_by or "system"
        )
        return self.content_service.save_content(chat_log)
    
    def record_scene_conclusion(
        self,
        scene_id: str,
        universe_id: str,
        what_happened: str,
        key_decisions: str | None = None,
        character_developments: str | None = None,
        plot_threads: str | None = None,
        consequences: str | None = None,
        created_by: str = "narrator"
    ) -> str:
        """Record scene abstract/conclusion."""
        abstract = SceneAbstract(
            universe_id=universe_id,
            scene_id=scene_id,
            linked_scene_id=scene_id,
            title=f"Scene Summary",
            content=what_happened,
            what_happened=what_happened,
            key_decisions=key_decisions,
            character_developments=character_developments,
            plot_threads=plot_threads,
            consequences=consequences,
            created_by=created_by
        )
        return self.content_service.save_content(abstract)
    
    def record_gm_note(
        self,
        universe_id: str,
        content: str,
        note_type: str = "general",
        priority: str = "normal",
        tags: list[str] | None = None,
        trigger_conditions: str | None = None,
        created_by: str = "narrator"
    ) -> str:
        """Record a GM note for future reference."""
        note = GMNote(
            universe_id=universe_id,
            content=content,
            note_type=note_type,
            priority=priority,
            tags=tags or [],
            trigger_conditions=trigger_conditions,
            created_by=created_by
        )
        return self.content_service.save_content(note)
    
    def update_narrative_state(
        self,
        universe_id: str,
        current_tone: str | None = None,
        active_plot_threads: list[str] | None = None,
        tension_level: int | None = None,
        pacing: str | None = None,
        unresolved_questions: list[str] | None = None,
        pending_consequences: list[str] | None = None,
        created_by: str = "narrator"
    ) -> str:
        """Update the current narrative state."""
        state = NarrativeState(
            universe_id=universe_id,
            title="Current Narrative State",
            content=f"Narrative state updated by {created_by}",
            current_tone=current_tone,
            active_plot_threads=active_plot_threads or [],
            tension_level=tension_level,
            pacing=pacing,
            unresolved_questions=unresolved_questions or [],
            pending_consequences=pending_consequences or [],
            created_by=created_by
        )
        return self.content_service.save_content(state)
    
    def update_character_memory(
        self,
        character_id: str,
        universe_id: str,
        personal_memories: str | None = None,
        relationships_memory: str | None = None,
        secrets_known: str | None = None,
        goals_and_motivations: str | None = None,
        confidence_level: float = 1.0,
        last_updated_scene: str | None = None,
        created_by: str = "system"
    ) -> str:
        """Update character memory and context."""
        memory = CharacterMemory(
            universe_id=universe_id,
            character_id=character_id,
            linked_entity_ids=[character_id],
            title=f"Memory for {character_id}",
            content=f"Character memory updated by {created_by}",
            personal_memories=personal_memories,
            relationships_memory=relationships_memory,
            secrets_known=secrets_known,
            goals_and_motivations=goals_and_motivations,
            confidence_level=confidence_level,
            last_updated_scene=last_updated_scene,
            created_by=created_by
        )
        return self.content_service.save_content(memory)
