# English version of historia.py

from uuid import uuid4

from pydantic import BaseModel, Field

from core.domain.event import Event
from core.domain.scene import Scene
from core.domain.sheet import Sheet


class Story(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    summary: str | None = None
    events: list[Event] = Field(default_factory=list)
    sheets: list[Sheet] = Field(default_factory=list)
    scenes: list[Scene] = Field(default_factory=list)
    universe_id: str | None = None
    arc_id: str | None = None
    system_id: str | None = None  # USES_SYSTEM at Story scope overrides Universe
