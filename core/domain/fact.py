from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class FactParticipant(BaseModel):
    entity_id: str
    role: str | None = None


class Fact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    universe_id: str | None = None
    description: str
    when: str | None = None
    time_span: dict[str, Any] | None = None
    occurs_in: str | None = None  # Scene ID
    participants: list[FactParticipant] = Field(default_factory=list)
    source_refs: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float | None = None
    derived_from: list[str] = Field(default_factory=list)


class RelationState(BaseModel):
    id: str
    type: str
    entity_a: str
    entity_b: str
    started_at: str | None = None
    ended_at: str | None = None
    set_in_scene: str | None = None
    changed_in_scene: str | None = None
    ended_in_scene: str | None = None
