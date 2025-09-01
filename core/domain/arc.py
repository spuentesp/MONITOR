from uuid import uuid4

from pydantic import BaseModel, Field


class Arc(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    universe_id: str
    story_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    entity_ids: list[str] = Field(default_factory=list)
    # Optional span in world time; structure kept flexible for now
    time_span: dict | None = None
    # narrative|chronological|mixed
    ordering_mode: str | None = None
