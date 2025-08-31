# English version of historia.py

from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4

from core.domain.event import Event
from core.domain.sheet import Sheet

class Story(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    summary: Optional[str] = None
    events: List[Event] = Field(default_factory=list)
    sheets: List[Sheet] = Field(default_factory=list)
    universe_id: Optional[str] = None
    arc_id: Optional[str] = None
    system_id: Optional[str] = None  # USES_SYSTEM at Story scope overrides Universe
