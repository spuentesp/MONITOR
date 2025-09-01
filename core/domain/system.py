from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel


class System(BaseModel):
    id: str
    name: str
    version: Optional[str] = None
    description: Optional[str] = None
    dice_pool: List[str] = []
    stats: List[Union[str, Dict[str, Any]]] = []
    resources: List[Union[str, Dict[str, Any]]] = []
    conditions: List[Union[str, Dict[str, Any]]] = []
    tags: List[Union[str, Dict[str, Any]]] = []
    actions: List[Union[str, Dict[str, Any]]] = []
    roll_mechanic: Optional[Union[str, Dict[str, Any]]] = None
    resolution_rules: List[Union[str, Dict[str, Any]]] = []
    progression: Optional[Dict[str, Any]] = None
    character_creation: Optional[Dict[str, Any]] = None
    critical_rules: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}
