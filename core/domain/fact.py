from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import uuid4


class FactParticipant(BaseModel):
    entity_id: str
    role: Optional[str] = None


class Fact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    universe_id: Optional[str] = None
    description: str
    when: Optional[str] = None
    time_span: Optional[Dict[str, Any]] = None
    occurs_in: Optional[str] = None  # Scene ID
    participants: List[FactParticipant] = Field(default_factory=list)
    source_refs: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: Optional[float] = None
    derived_from: List[str] = Field(default_factory=list)


class RelationState(BaseModel):
    id: str
    type: str
    entity_a: str
    entity_b: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    set_in_scene: Optional[str] = None
    changed_in_scene: Optional[str] = None
    ended_in_scene: Optional[str] = None
