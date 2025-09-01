# English version of universo.py

from uuid import uuid4

from pydantic import BaseModel, Field

from core.domain.arc import Arc
from core.domain.axiom import Axiom
from core.domain.entity import ArchetypeEntity, ConcreteEntity
from core.domain.fact import Fact, RelationState
from core.domain.story import Story


class Universe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str | None = None
    stories: list[Story] = Field(default_factory=list)
    arcs: list[Arc] = Field(default_factory=list)
    entities: list[ConcreteEntity] = Field(default_factory=list)
    multiverse_id: str | None = None
    system_id: str | None = None  # USES_SYSTEM at Universe scope
    # Ontology attachments at universe scope
    axioms: list[Axiom] = Field(default_factory=list)
    archetypes: list[ArchetypeEntity] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    relation_states: list[RelationState] = Field(default_factory=list)
