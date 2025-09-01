# English version of modelo_base.py

from pydantic import BaseModel as PydBaseModel
from pydantic import ConfigDict


class BaseModel(PydBaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
