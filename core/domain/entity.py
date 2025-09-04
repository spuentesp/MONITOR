from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from core.domain.sheet import Sheet
from core.domain.sheet import Sheet


class ArchetypeEntity(BaseModel):
    id: str
    name: str
    description: str | None = None
    type: str | None = Field(default="concept")  # e.g., "character", "place", "idea"
    attributes: dict[str, str] = Field(default_factory=dict)
    relations: dict[str, str] = Field(default_factory=dict)  # e.g., {"enemy_of": "axiom-002"}


class ConcreteEntity(BaseModel):
    id: str
    name: str
    universe_id: str  # To trace the universe where it lives
    archetype_id: str | None = None  # If derived from an ArchetypeEntity
    type: str | None = Field(default="manifestation")
    attributes: dict[str, str] = Field(default_factory=dict)
    story: list[str] = Field(default_factory=list)  # References to events or observations
    relations: dict[str, str] = Field(default_factory=dict)  # e.g., {"ally_of": "concrete-103"}
    system_id: str | None = None
    sheets: list[Sheet] = Field(default_factory=list)
    # Pydantic v2 config
    model_config = ConfigDict(arbitrary_types_allowed=True)
