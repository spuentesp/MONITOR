from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")


class NewMultiverse(_Base):
    id: str | None = None
    name: str | None = None
    description: str | None = None
    omniverse_id: str | None = None


class NewUniverse(_Base):
    id: str | None = None
    name: str | None = None
    description: str | None = None
    multiverse_id: str | None = None


class NewArc(_Base):
    id: str | None = None
    title: str | None = None
    tags: list[str] | None = None
    ordering_mode: Literal["sequence", "time", "custom"] | None = None
    universe_id: str | None = None


class NewStory(_Base):
    id: str | None = None
    title: str | None = None
    summary: str | None = None
    universe_id: str | None = None
    arc_id: str | None = None
    sequence_index: int | None = None
    tags: list[str] | None = None


class NewScene(_Base):
    id: str | None = None
    title: str | None = None
    story_id: str | None = None
    sequence_index: int | None = None
    when: str | None = None
    time_span: Any | None = None
    recorded_at: str | None = None
    location: str | None = None
    participants: list[str] | None = None


class NewEntity(_Base):
    id: str | None = None
    name: str | None = None
    type: str | None = None
    universe_id: str | None = None
    attributes: dict[str, Any] | None = None


class FactParticipant(_Base):
    entity_id: str
    role: str | None = None


class FactDelta(_Base):
    id: str | None = None
    universe_id: str | None = None
    description: str | None = None
    when: str | None = None
    time_span: Any | None = None
    confidence: float | None = None
    derived_from: Any | None = None
    occurs_in: str | None = None
    participants: list[FactParticipant] | None = None
    evidence: list[dict[str, Any] | str] | None = None


class RelationStateDelta(_Base):
    id: str | None = None
    type: str | None = None
    entity_a: str | None = Field(None, description="Entity ID A")
    entity_b: str | None = Field(None, description="Entity ID B")
    started_at: str | None = None
    ended_at: str | None = None
    set_in_scene: str | None = None
    changed_in_scene: str | None = None
    ended_in_scene: str | None = None


class RelationEdge(_Base):
    a: str | None = None
    b: str | None = None
    type: str | None = None
    weight: float | None = None
    temporal: dict[str, Any] | None = None

    # Accept legacy keys {from,to} by alias
    def model_post_init(self, context: Any) -> None:
        # Coalesce legacy keys
        if self.a is None and hasattr(self, "from"):
            object.__setattr__(self, "a", getattr(self, "from"))
        if self.b is None and hasattr(self, "to"):
            object.__setattr__(self, "b", self.to)


class DeltaBatch(_Base):
    scene_id: str | None = None
    facts: list[FactDelta] | None = None
    relation_states: list[RelationStateDelta] | None = None
    relations: list[RelationEdge] | None = None
    universe_id: str | None = None
    new_multiverse: NewMultiverse | None = None
    new_universe: NewUniverse | None = None
    new_arc: NewArc | None = None
    new_story: NewStory | None = None
    new_scene: NewScene | None = None
    new_entities: list[NewEntity] | None = None
