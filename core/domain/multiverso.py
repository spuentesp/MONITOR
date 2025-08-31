from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4

from core.domain.modelo_base import ModeloBase
from core.domain.universo import Universo


class Multiverso(ModeloBase):
    id: str = Field(default_factory=lambda: str(uuid4()))
    nombre: str
    descripcion: Optional[str] = None
    universos: List[Universo] = Field(default_factory=list)
    omniverso_id: Optional[str] = None
