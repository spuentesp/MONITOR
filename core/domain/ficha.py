from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import uuid4


class Ficha(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    nombre: str
    tipo: str  # Ej: "PJ", "PNJ", "Entidad", "Lugar", "Objeto"
    atributos: Dict[str, Any] = Field(default_factory=dict)
    historia_local: List[str] = Field(default_factory=list)  # Lista de IDs de eventos
    entidad_id: Optional[str] = None  # Relación con una EntidadConcreta
    historia_id: Optional[str] = None  # Historia donde se encuentra activa
