from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import uuid4
from core.domain.modelo_base import ModeloBase


class Evento(ModeloBase):
    id: str = Field(default_factory=lambda: str(uuid4()))
    titulo: Optional[str] = None
    descripcion: str
    tipo: str  # Ej: "narrativo", "interactivo", "sistema", "meta"
    participantes: List[str] = Field(default_factory=list)  # IDs de EntidadConcreta
    consecuencias: Optional[Dict[str, Any]] = None  # Efectos narrativos o mecánicos
    universo_id: Optional[str] = None  # ID del universo donde ocurre
    historia_id: Optional[str] = None  # ID de la historia asociada
    orden: Optional[int] = None  # Para representar secuencialidad si se requiere
