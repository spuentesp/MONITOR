from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Scene(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    story_id: str | None = None
    sequence_index: int | None = None
    when: str | None = None  # world time instant
    time_span: dict[str, Any] | None = None  # {started_at, ended_at}
    recorded_at: str | None = None  # session time
    location: str | None = None
    participants: list[str] = Field(default_factory=list)  # Entity IDs appearing in scene
