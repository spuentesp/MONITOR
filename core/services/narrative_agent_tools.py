"""
Enhanced agent tooling for narrative content integration.

Extends agents with rich narrative content capabilities.
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
    """Provides rich context to agents from narrative content."""
    
    def __init__(self, content_service: NarrativeContentService):
        self.content_service = content_service
    
    def get_scene_context(self, scene_id: str, universe_id: str) -> dict[str, Any]:
        """Get comprehensive context for a scene."""
        context = {
            "chat_logs": self.content_service.get_scene_chat_logs(scene_id),
            "scene_abstract": self.content_service.get_scene_abstract(scene_id),
            "narrative_state": self.content_service.get_narrative_state(universe_id),
            "active_gm_notes": self.content_service.get_active_gm_notes(universe_id),
        }
        return context
    
    def get_character_context(self, character_id: str, universe_id: str) -> dict[str, Any]:
        """Get comprehensive context for a character."""
        context = {
            "description": self.content_service.get_entity_description(character_id),
            "memory": self.content_service.get_character_memory(character_id),
            "related_notes": self.content_service.get_active_gm_notes(
                universe_id, tags=[f"character:{character_id}"]
            ),
        }
        return context
    
    def get_narrator_context(self, universe_id: str, scene_id: str | None = None) -> dict[str, Any]:
        """Get context specifically useful for the Narrator agent."""
        context = {
            "narrative_state": self.content_service.get_narrative_state(universe_id),
            "gm_notes": self.content_service.get_active_gm_notes(universe_id),
            "content_stats": self.content_service.get_content_stats(universe_id),
        }
        
        if scene_id:
            context.update(self.get_scene_context(scene_id, universe_id))
        
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
