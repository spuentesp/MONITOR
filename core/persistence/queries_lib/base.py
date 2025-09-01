from __future__ import annotations

from typing import Any, Dict, List


class BaseQueries:
    def __init__(self, repo):
        self.repo = repo

    def _rows(self, text: str, **params) -> List[Dict[str, Any]]:
        rows = self.repo.run(text, **params)
        return [dict(r) for r in rows]
