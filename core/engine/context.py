from pydantic import BaseModel
from typing import Optional, Literal

class ContextToken(BaseModel):
    omniverse_id: str
    multiverse_id: str
    universe_id: str
    time_ref: Optional[str] = None
    mode: Literal['read', 'write', 'observe'] = 'read'

