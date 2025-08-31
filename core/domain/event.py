# English version of evento.py

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import uuid4

class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: Optional[str] = None
    description: str
    type: str  # E.g.: "narrative", "interactive", "system", "meta"
    participants: List[str] = Field(default_factory=list)  # IDs of ConcreteEntity
    consequences: Optional[Dict[str, Any]] = None  # Narrative or mechanical effects
    universe_id: Optional[str] = None  # Universe where it occurs
    story_id: Optional[str] = None  # Associated story
    system_id: Optional[str] = None  # Active system at event time (optional)
    order: Optional[int] = None  # For sequence if needed
