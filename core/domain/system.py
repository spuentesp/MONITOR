from typing import Any

from pydantic import BaseModel


class System(BaseModel):
    id: str
    name: str
    version: str | None = None
    description: str | None = None
    dice_pool: list[str] = []
    stats: list[str | dict[str, Any]] = []
    resources: list[str | dict[str, Any]] = []
    conditions: list[str | dict[str, Any]] = []
    tags: list[str | dict[str, Any]] = []
    actions: list[str | dict[str, Any]] = []
    roll_mechanic: str | dict[str, Any] | None = None
    resolution_rules: list[str | dict[str, Any]] = []
    progression: dict[str, Any] | None = None
    character_creation: dict[str, Any] | None = None
    critical_rules: dict[str, Any] | None = None
    metadata: dict[str, Any] = {}
