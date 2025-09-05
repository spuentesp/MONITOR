"""Simple context token for API authentication and universe selection."""

from __future__ import annotations

from pydantic import BaseModel


class ContextToken(BaseModel):
    """Token for API authentication and context selection."""
    
    omniverse_id: str
    multiverse_id: str 
    universe_id: str
    mode: str = "read"


__all__ = ["ContextToken"]
