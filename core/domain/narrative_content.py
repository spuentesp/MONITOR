"""
Narrative content models for MongoDB storage.

These models capture rich text descriptions, chat logs, and narrative data
that complement the graph ontology.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Types of narrative content."""

    DESCRIPTION = "description"
    CHAT_LOG = "chat_log"
    SCENE_ABSTRACT = "scene_abstract"
    GM_NOTE = "gm_note"
    NARRATIVE_STATE = "narrative_state"
    CHARACTER_MEMORY = "character_memory"


class NarrativeContent(BaseModel):
    """Base model for all narrative content stored in MongoDB."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    content_type: ContentType
    universe_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str | None = None  # agent or user ID

    # Links to graph entities
    linked_entity_ids: list[str] = Field(default_factory=list)
    linked_scene_id: str | None = None
    linked_story_id: str | None = None

    # Content payload
    title: str | None = None
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntityDescription(NarrativeContent):
    """Rich text description of a graph entity."""

    content_type: ContentType = ContentType.DESCRIPTION
    entity_id: str

    # Rich description fields
    appearance: str | None = None
    personality: str | None = None
    backstory: str | None = None
    abilities: str | None = None
    relationships: str | None = None


class ChatLog(NarrativeContent):
    """Chat log entry for a scene or character interaction."""

    content_type: ContentType = ContentType.CHAT_LOG
    speaker_id: str | None = None  # entity ID or 'GM' or user ID
    speaker_name: str
    message_type: str = "dialogue"  # dialogue, action, ooc, system
    timestamp_in_scene: str | None = None


class SceneAbstract(NarrativeContent):
    """Summary and conclusion of a scene."""

    content_type: ContentType = ContentType.SCENE_ABSTRACT
    scene_id: str

    # Scene summary fields
    what_happened: str
    key_decisions: str | None = None
    character_developments: str | None = None
    plot_threads: str | None = None
    consequences: str | None = None


class GMNote(NarrativeContent):
    """Game Master notes and reminders."""

    content_type: ContentType = ContentType.GM_NOTE
    note_type: str = "general"  # general, reminder, plot_hook, npc_note
    priority: str = "normal"  # low, normal, high, critical

    # When this note should be surfaced
    trigger_conditions: str | None = None
    expires_at: datetime | None = None

    # Tags for organization
    tags: list[str] = Field(default_factory=list)


class NarrativeState(NarrativeContent):
    """Current narrative state and context."""

    content_type: ContentType = ContentType.NARRATIVE_STATE

    # Current narrative context
    current_tone: str | None = None
    active_plot_threads: list[str] = Field(default_factory=list)
    tension_level: int | None = None  # 1-10
    pacing: str | None = None  # slow, normal, fast, breakneck

    # Continuity tracking
    unresolved_questions: list[str] = Field(default_factory=list)
    pending_consequences: list[str] = Field(default_factory=list)


class CharacterMemory(NarrativeContent):
    """Character-specific memories and context."""

    content_type: ContentType = ContentType.CHARACTER_MEMORY
    character_id: str

    # Memory categories
    personal_memories: str | None = None
    relationships_memory: str | None = None
    secrets_known: str | None = None
    goals_and_motivations: str | None = None

    # Memory metadata
    confidence_level: float = 1.0  # How reliable this memory is
    last_updated_scene: str | None = None
