# English version of omniverso.py


from pydantic import BaseModel, Field

from core.domain.multiverse import Multiverse


class Omniverse(BaseModel):
    id: str = Field(default_factory=lambda: "omniverse-001")
    name: str = Field(default_factory=lambda: "M.O.N.I.T.O.R.")
    multiverses: list[Multiverse] = Field(default_factory=list)
