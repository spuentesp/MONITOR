from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4

from core.domain.historia import Historia
from core.domain.modelo_base import ModeloBase


class Universo(ModeloBase):
    id: str = Field(default_factory=lambda: str(uuid4()))
    nombre: str
    descripcion: Optional[str] = None
    historias: List[Historia] = Field(default_factory=list)
    multiverso_id: Optional[str] = None