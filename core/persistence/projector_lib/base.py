from __future__ import annotations

import json
from typing import Any


class ProjectorBase:
    def __init__(self, repo):
        self.repo = repo

    @staticmethod
    def _is_primitive(x):
        return isinstance(x, str | int | float | bool) or x is None

    @classmethod
    def _sanitize(cls, value: Any):
        if cls._is_primitive(value):
            return value
        if isinstance(value, list):
            if all(cls._is_primitive(i) for i in value):
                return value
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        return str(value)
