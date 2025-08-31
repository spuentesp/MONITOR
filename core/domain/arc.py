from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4


class Arc(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    universe_id: str
    story_ids: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    entity_ids: List[str] = Field(default_factory=list)
    # Optional span in world time; structure kept flexible for now
    time_span: Optional[dict] = None
    # narrative|chronological|mixed
    ordering_mode: Optional[str] = None
