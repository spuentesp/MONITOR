from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from core.domain.sheet import Sheet

class ArchetypeEntity(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    type: Optional[str] = Field(default="concept")  # e.g., "character", "place", "idea"
    attributes: Dict[str, str] = Field(default_factory=dict)
    relations: Dict[str, str] = Field(default_factory=dict)  # e.g., {"enemy_of": "axiom-002"}

class ConcreteEntity(BaseModel):
    id: str
    name: str
    universe_id: str  # To trace the universe where it lives
    archetype_id: Optional[str] = None  # If derived from an ArchetypeEntity
    type: Optional[str] = Field(default="manifestation")
    attributes: Dict[str, str] = Field(default_factory=dict)
    story: List[str] = Field(default_factory=list)  # References to events or observations
    relations: Dict[str, str] = Field(default_factory=dict)  # e.g., {"ally_of": "concrete-103"}
    system_id: Optional[str] = None
    sheets: List[Sheet] = Field(default_factory=list)
