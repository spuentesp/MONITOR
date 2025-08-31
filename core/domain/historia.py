from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4

from core.domain.evento import Evento
from core.domain.ficha import Ficha
from core.domain.modelo_base import ModeloBase


class Historia(ModeloBase):
    id: str = Field(default_factory=lambda: str(uuid4()))
    titulo: str
    resumen: Optional[str] = None
    eventos: List[Evento] = Field(default_factory=list)
    fichas: List[Ficha] = Field(default_factory=list)
    universo_id: Optional[str] = None
