from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

# Pydantic-first builders leveraging core.domain.deltas
from core.domain.deltas import (
    DeltaBatch,
    FactDelta,
    FactParticipant,
    NewEntity,
    NewScene,
    NewStory,
    NewUniverse,
)


def uid(prefix: str) -> str:
    return f"{prefix}:{uuid4().hex[:8]}"


@dataclass
class UniverseFactory:
    id: str | None = None
    name: str = "Test Universe"

    def build(self) -> dict[str, Any]:
        # Keep dict output for existing tests
        return {"id": self.id or uid("universe"), "name": self.name}

    def model(self) -> NewUniverse:
        return NewUniverse(id=self.id or uid("universe"), name=self.name)


@dataclass
class StoryFactory:
    universe_id: str
    id: str | None = None
    title: str = "Test Story"
    sequence_index: int | None = 1

    def build(self) -> dict[str, Any]:
        return {
            "id": self.id or uid("story"),
            "title": self.title,
            "universe_id": self.universe_id,
            "sequence_index": self.sequence_index,
        }

    def model(self) -> NewStory:
        return NewStory(
            id=self.id or uid("story"),
            title=self.title,
            universe_id=self.universe_id,
            sequence_index=self.sequence_index,
        )


@dataclass
class SceneFactory:
    story_id: str
    id: str | None = None
    title: str = "Scene"
    sequence_index: int | None = 1

    def build(self) -> dict[str, Any]:
        return {
            "id": self.id or uid("scene"),
            "title": self.title,
            "story_id": self.story_id,
            "sequence_index": self.sequence_index,
        }

    def model(self) -> NewScene:
        return NewScene(
            id=self.id or uid("scene"),
            title=self.title,
            story_id=self.story_id,
            sequence_index=self.sequence_index,
        )


@dataclass
class EntityFactory:
    universe_id: str
    id: str | None = None
    name: str = "NPC"
    type: str | None = None

    def build(self) -> dict[str, Any]:
        return {
            "id": self.id or uid("entity"),
            "name": self.name,
            "type": self.type,
            "universe_id": self.universe_id,
        }

    def model(self) -> NewEntity:
        return NewEntity(
            id=self.id or uid("entity"),
            name=self.name,
            type=self.type,
            universe_id=self.universe_id,
        )


@dataclass
class FactFactory:
    description: str
    occurs_in: str | None = None
    universe_id: str | None = None
    participants: list[dict[str, Any]] | None = None

    def build(self) -> dict[str, Any]:
        out = {"description": self.description}
        if self.occurs_in:
            out["occurs_in"] = self.occurs_in
        if self.universe_id:
            out["universe_id"] = self.universe_id
        if self.participants:
            out["participants"] = self.participants
        return out

    def model(self) -> FactDelta:
        parts = None
        if self.participants:
            parts = [
                (p if isinstance(p, FactParticipant) else FactParticipant(**p))  # type: ignore[arg-type]
                for p in self.participants
            ]
        return FactDelta(
            description=self.description,
            occurs_in=self.occurs_in,
            universe_id=self.universe_id,
            participants=parts,
        )


def batch(
    *,
    scene_id: str | None = None,
    universe_id: str | None = None,
    facts: list[FactFactory] | None = None,
    new_universe: UniverseFactory | None = None,
    new_story: StoryFactory | None = None,
    new_scene: SceneFactory | None = None,
    new_entities: list[EntityFactory] | None = None,
) -> DeltaBatch:
    return DeltaBatch(
        scene_id=scene_id,
        universe_id=universe_id,
        facts=[f.model() for f in (facts or [])] or None,
        new_universe=new_universe.model() if new_universe else None,
        new_story=new_story.model() if new_story else None,
        new_scene=new_scene.model() if new_scene else None,
        new_entities=[e.model() for e in (new_entities or [])] or None,
    )
