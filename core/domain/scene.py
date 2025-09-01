from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import uuid4


class Scene(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    story_id: Optional[str] = None
    sequence_index: Optional[int] = None
    when: Optional[str] = None  # world time instant
    time_span: Optional[Dict[str, Any]] = None  # {started_at, ended_at}
    recorded_at: Optional[str] = None  # session time
    location: Optional[str] = None
    participants: List[str] = Field(default_factory=list)  # Entity IDs appearing in scene