# English version of omniverso.py

from typing import List
from pydantic import BaseModel, Field
from core.domain.multiverse import Multiverse


class Omniverse(BaseModel):
    id: str = "omniverse-001"
    name: str = "M.O.N.I.T.O.R."
    multiverses: List[Multiverse] = Field(default_factory=list)
