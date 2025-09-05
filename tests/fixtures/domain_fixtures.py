"""
Domain model fixtures and builders for testing.

Provides builders for Pydantic models and domain objects
that create valid test data easily.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from core.domain.deltas import (
    DeltaBatch,
    FactDelta,
    FactParticipant,
    NewEntity,
    NewScene,
    NewStory,
    NewUniverse,
)


def test_id(prefix: str = "test") -> str:
    """Generate a test ID with prefix."""
    return f"{prefix}:{uuid4().hex[:8]}"


def build_test_universe(
    id: str | None = None,
    name: str = "Test Universe",
    description: str = "A universe for testing",
    multiverse_id: str | None = None
) -> NewUniverse:
    """Build a test Universe object."""
    return NewUniverse(
        id=id or test_id("universe"),
        name=name,
        description=description,
        multiverse_id=multiverse_id or test_id("multiverse")
    )


def build_test_story(
    id: str | None = None,
    title: str = "Test Story",
    summary: str = "A story for testing",
    universe_id: str | None = None
) -> NewStory:
    """Build a test Story object."""
    return NewStory(
        id=id or test_id("story"),
        title=title,
        summary=summary,
        universe_id=universe_id or test_id("universe")
    )


def build_test_scene(
    id: str | None = None,
    story_id: str | None = None,
    universe_id: str | None = None,
    sequence_index: int = 1,
    when: str = "Present day",
    location: str = "Test location"
) -> NewScene:
    """Build a test Scene object."""
    return NewScene(
        id=id or test_id("scene"),
        story_id=story_id or test_id("story"),
        universe_id=universe_id or test_id("universe"),
        sequence_index=sequence_index,
        when=when,
        location=location
    )


def build_test_entity(
    id: str | None = None,
    name: str = "Test Entity",
    entity_type: str = "character",
    universe_id: str | None = None,
    description: str = "An entity for testing"
) -> NewEntity:
    """Build a test Entity object."""
    return NewEntity(
        id=id or test_id("entity"),
        name=name,
        type=entity_type,
        universe_id=universe_id or test_id("universe"),
        description=description
    )


def build_test_fact(
    id: str | None = None,
    description: str = "Test fact description",
    universe_id: str | None = None,
    occurs_in: str | None = None,
    participants: list[FactParticipant] | None = None
) -> FactDelta:
    """Build a test FactDelta object."""
    return FactDelta(
        id=id or test_id("fact"),
        description=description,
        universe_id=universe_id or test_id("universe"),
        occurs_in=occurs_in or test_id("scene"),
        participants=participants or []
    )


def build_test_fact_delta(
    fact: FactDelta | None = None,
    participants: list[FactParticipant] | None = None
) -> FactDelta:
    """Build a test FactDelta object."""
    return fact or FactDelta(
        participants=participants or []
    )


def build_test_deltas(
    new_universe: NewUniverse | None = None,
    new_story: NewStory | None = None, 
    new_scene: NewScene | None = None,
    new_entities: list[NewEntity] | None = None,
    fact_deltas: list[FactDelta] | None = None
) -> DeltaBatch:
    """Build a test DeltaBatch object."""
    return DeltaBatch(
        new_universe=new_universe,
        new_story=new_story,
        new_scene=new_scene,
        new_entities=new_entities or [],
        fact_deltas=fact_deltas or []
    )


def build_test_participant(
    entity_id: str | None = None,
    role: str = "participant"
) -> FactParticipant:
    """Build a test FactParticipant object.""" 
    return FactParticipant(
        entity_id=entity_id or test_id("entity"),
        role=role
    )


# Convenience builders for complex scenarios
def build_story_with_scenes(
    story_title: str = "Test Story",
    scene_count: int = 3,
    universe_id: str | None = None
) -> tuple[NewStory, list[NewScene]]:
    """Build a story with multiple scenes."""
    story = build_test_story(title=story_title, universe_id=universe_id)
    scenes = [
        build_test_scene(
            story_id=story.id,
            universe_id=story.universe_id,
            sequence_index=i + 1,
            location=f"Location {i + 1}"
        )
        for i in range(scene_count)
    ]
    return story, scenes


def build_scene_with_entities(
    scene: NewScene | None = None,
    entity_count: int = 2
) -> tuple[NewScene, list[NewEntity]]:
    """Build a scene with multiple entities."""
    if scene is None:
        scene = build_test_scene()
    
    entities = [
        build_test_entity(
            name=f"Character {i + 1}",
            universe_id=scene.universe_id
        )
        for i in range(entity_count)
    ]
    return scene, entities