from typing import Any

from pydantic import BaseModel, Field


class Axiom(BaseModel):
    id: str
    type: str  # e.g., "universal" | "probabilistic" | "conditional"
    semantics: str  # e.g., "existence" | "constraint" | "implication" | "min_count"
    description: str | None = None
    # Optional numeric semantics
    probability: float | None = None
    min_count: int | None = None
    # References
    refers_to_archetype: str | None = None
    refers_to: dict[str, Any] = Field(default_factory=dict)  # future-proof extra references
    # Scope bindings (universe ids)
    applies_to: list[str] = Field(default_factory=list)
    # Lifecycle
    enabled: bool = True
