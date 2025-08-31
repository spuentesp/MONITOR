from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class System(BaseModel):
    id: str
    name: str
    version: Optional[str] = None
    description: Optional[str] = None
    dice_pool: List[str] = []
    stats: List[Dict[str, Any]] = []
    resources: List[Dict[str, Any]] = []
    conditions: List[Dict[str, Any]] = []
    tags: List[Dict[str, Any]] = []
    actions: List[Dict[str, Any]] = []
    roll_mechanic: Optional[Dict[str, Any]] = None
    resolution_rules: List[Dict[str, Any]] = []
    progression: Optional[Dict[str, Any]] = None
    character_creation: Optional[Dict[str, Any]] = None
    critical_rules: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}
