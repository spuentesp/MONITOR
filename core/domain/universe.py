# English version of universo.py

from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4

from core.domain.story import Story
from typing import Optional

class Universe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    stories: List[Story] = Field(default_factory=list)
    multiverse_id: Optional[str] = None
    system_id: Optional[str] = None  # USES_SYSTEM at Universe scope
