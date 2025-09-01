from typing import Literal

from pydantic import BaseModel


class ContextToken(BaseModel):
    omniverse_id: str
    multiverse_id: str
    universe_id: str
    time_ref: str | None = None
    mode: Literal["read", "write", "observe"] = "read"
