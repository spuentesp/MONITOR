from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from core.ports.storage import RepoPort
except ImportError:  # pragma: no cover
    RepoPort = Any  # type: ignore

from core.services.projection import ProjectionService


class Projector:
    """
    Projects domain models to persistence layer using composition pattern.
    """

    def __init__(self, repo: Any):  # duck-typed to RepoPort | Neo4jRepo when available
        self.repo = repo
        self._service = ProjectionService(repo)

    def project_from_yaml(self, yaml_path: Path | str, ensure_constraints: bool = True) -> None:
        """Project a complete omniverse from YAML."""
        return self._service.project_from_yaml(yaml_path, ensure_constraints)
