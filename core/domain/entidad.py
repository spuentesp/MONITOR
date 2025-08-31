from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from core.domain.modelo_base import ModeloBase


class EntidadAxiomatica(ModeloBase):
    id: str
    nombre: str
    descripcion: Optional[str] = None
    tipo: Optional[str] = Field(default="concepto")  # e.g., "personaje", "lugar", "idea"
    atributos: Dict[str, str] = Field(default_factory=dict)
    relaciones: Dict[str, str] = Field(default_factory=dict)  # e.g., {"enemigo_de": "axioma-002"}


class EntidadConcreta(ModeloBase):
    id: str
    nombre: str
    universo_id: str  # Para trazar el universo donde vive
    axioma_id: Optional[str] = None  # Si deriva de una EntidadAxiomatica
    tipo: Optional[str] = Field(default="manifestacion")
    atributos: Dict[str, str] = Field(default_factory=dict)
    historia: List[str] = Field(default_factory=list)  # Referencias a eventos u observaciones
    relaciones: Dict[str, str] = Field(default_factory=dict)  # e.g., {"aliado_de": "concreta-103"}
