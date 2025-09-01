from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Axiom(BaseModel):
    id: str
    type: str  # e.g., "universal" | "probabilistic" | "conditional"
    semantics: str  # e.g., "existence" | "constraint" | "implication" | "min_count"
    description: Optional[str] = None
    # Optional numeric semantics
    probability: Optional[float] = None
    min_count: Optional[int] = None
    # References
    refers_to_archetype: Optional[str] = None
    refers_to: Dict[str, Any] = Field(default_factory=dict)  # future-proof extra references
    # Scope bindings (universe ids)
    applies_to: List[str] = Field(default_factory=list)
    # Lifecycle
    enabled: bool = True
