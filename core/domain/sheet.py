# English version of ficha.py

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import uuid4

class Sheet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    type: str  # E.g.: "PC", "NPC", "Entity", "Place", "Object"
    attributes: Dict[str, Any] = Field(default_factory=dict)
    local_story: List[str] = Field(default_factory=list)  # List of event IDs
    entity_id: Optional[str] = None  # Relation to a ConcreteEntity
    story_id: Optional[str] = None  # Story where active
    system_id: Optional[str] = None  # Bound ruleset
