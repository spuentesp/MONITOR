# core/domain/base.py
from pydantic import BaseModel

class ModeloBase(BaseModel):
    model_config = {
        "arbitrary_types_allowed": True
    }
