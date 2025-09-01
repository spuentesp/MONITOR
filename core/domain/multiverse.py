# English version of multiverso.py

from uuid import uuid4

from pydantic import BaseModel, Field

from core.domain.axiom import Axiom
from core.domain.entity import ArchetypeEntity
from core.domain.universe import Universe


class Multiverse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str | None = None
    universes: list[Universe] = Field(default_factory=list)
    omniverse_id: str | None = None
    # Ontology attachments at multiverse scope
    axioms: list[Axiom] = Field(default_factory=list)
    archetypes: list[ArchetypeEntity] = Field(default_factory=list)
