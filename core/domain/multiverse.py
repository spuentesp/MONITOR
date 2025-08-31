# English version of multiverso.py

from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4

from core.domain.universe import Universe

class Multiverse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    universes: List[Universe] = Field(default_factory=list)
    omniverse_id: Optional[str] = None
