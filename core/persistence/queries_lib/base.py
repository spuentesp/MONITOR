from __future__ import annotations

from typing import Any

try:
    from core.ports.storage import RepoPort  # type: ignore
except Exception:  # pragma: no cover
    RepoPort = Any  # type: ignore


class BaseQueries:
    def __init__(self, repo: RepoPort | Any):  # duck-typed to RepoPort
        self.repo = repo

    def _rows(self, text: str, **params: Any) -> list[dict[str, Any]]:
        rows = self.repo.run(text, **params)
        return [dict(r) for r in rows]
