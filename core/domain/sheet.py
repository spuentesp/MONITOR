# English version of ficha.py

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Sheet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    type: str  # E.g.: "PC", "NPC", "Entity", "Place", "Object"
    attributes: dict[str, Any] = Field(default_factory=dict)
    local_story: list[str] = Field(default_factory=list)  # List of event IDs
    entity_id: str | None = None  # Relation to a ConcreteEntity
    story_id: str | None = None  # Story where active
    system_id: str | None = None  # Bound ruleset
