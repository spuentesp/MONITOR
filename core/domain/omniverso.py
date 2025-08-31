from typing import List, Optional
from core.domain.modelo_base import ModeloBase
from core.domain.multiverso import Multiverso


class Omniverso(ModeloBase):
    id: str = "omniverso-001"
    nombre: str = "M.O.N.I.T.O.R."
    multiversos: List[Multiverso] = []