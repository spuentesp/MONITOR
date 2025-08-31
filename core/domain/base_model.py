# English version of modelo_base.py

from pydantic import BaseModel

class Config:
    arbitrary_types_allowed = True

class BaseModel(BaseModel):
    model_config = Config
