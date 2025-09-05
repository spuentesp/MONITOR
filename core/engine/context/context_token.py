"""
ContextToken for scoping operations to specific omniverse/multiverse/universe.
"""

from typing import Literal

from pydantic import BaseModel


class ContextToken(BaseModel):
    """Token that scopes operations to a specific context."""

    omniverse_id: str
    multiverse_id: str
    universe_id: str
    time_ref: str | None = None
    mode: Literal["read", "write", "observe"] = "read"
