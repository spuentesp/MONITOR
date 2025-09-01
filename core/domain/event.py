# English version of evento.py

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str | None = None
    description: str
    type: str  # E.g.: "narrative", "interactive", "system", "meta"
    participants: list[str] = Field(default_factory=list)  # IDs of ConcreteEntity
    consequences: dict[str, Any] | None = None  # Narrative or mechanical effects
    universe_id: str | None = None  # Universe where it occurs
    story_id: str | None = None  # Associated story
    system_id: str | None = None  # Active system at event time (optional)
    order: int | None = None  # For sequence if needed
