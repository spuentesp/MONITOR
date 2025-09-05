from __future__ import annotations

from typing import Any

try:
    from core.ports.storage import RepoPort
except ImportError:  # pragma: no cover
    RepoPort = Any  # type: ignore

from core.services.branching import BrancherService


class BranchService:
    """
    What-if branching and cloning operations for Universes.
    Uses composition pattern with dedicated service components.
    """

    def __init__(self, repo: Any):  # duck-typed to RepoPort | Neo4jRepo when available
        self.repo = repo
        self._service = BrancherService(repo)

    def clone_full(
        self,
        source_universe_id: str,
        new_universe_id: str,
        new_universe_name: str | None = None,
        *,
        force: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Clone a universe with all its content."""
        return self._service.clone_full(
            source_universe_id=source_universe_id,
            new_universe_id=new_universe_id,
            new_universe_name=new_universe_name,
            force=force,
            dry_run=dry_run,
        )

    def clone_subset(
        self,
        source_universe_id: str,
        new_universe_id: str,
        new_universe_name: str | None = None,
        stories: list[str] | None = None,
        arcs: list[str] | None = None,
        scene_max_index: int | None = None,
        include_all_entities: bool = False,
        *,
        force: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Clone a subset of a universe."""
        return self._service.clone_subset(
            source_universe_id=source_universe_id,
            new_universe_id=new_universe_id,
            new_universe_name=new_universe_name,
            stories=stories,
            arcs=arcs,
            scene_max_index=scene_max_index,
            include_all_entities=include_all_entities,
            force=force,
            dry_run=dry_run,
        )

    def branch_at_scene(
        self,
        source_universe_id: str,
        scene_id: str,
        new_universe_id: str,
        new_universe_name: str | None = None,
        *,
        force: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Create a branch of a universe starting at a specific scene."""
        return self._service.branch_at_scene(
            source_universe_id=source_universe_id,
            scene_id=scene_id,
            new_universe_id=new_universe_id,
            new_universe_name=new_universe_name,
            force=force,
            dry_run=dry_run,
        )

    # Legacy method names for backward compatibility
    def clone_universe_full(
        self,
        source_universe_id: str,
        new_universe_id: str,
        new_universe_name: str | None = None,
        *,
        force: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Legacy alias for clone_full."""
        return self.clone_full(
            source_universe_id=source_universe_id,
            new_universe_id=new_universe_id,
            new_universe_name=new_universe_name,
            force=force,
            dry_run=dry_run,
        )

    def clone_universe_subset(
        self,
        source_universe_id: str,
        new_universe_id: str,
        new_universe_name: str | None = None,
        stories: list[str] | None = None,
        arcs: list[str] | None = None,
        scene_max_index: int | None = None,
        include_all_entities: bool = False,
        *,
        force: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Legacy alias for clone_subset."""
        return self.clone_subset(
            source_universe_id=source_universe_id,
            new_universe_id=new_universe_id,
            new_universe_name=new_universe_name,
            stories=stories,
            arcs=arcs,
            scene_max_index=scene_max_index,
            include_all_entities=include_all_entities,
            force=force,
            dry_run=dry_run,
        )

    def branch_universe_at_scene(
        self,
        source_universe_id: str,
        scene_id: str,
        new_universe_id: str,
        new_universe_name: str | None = None,
        *,
        force: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Legacy alias for branch_at_scene."""
        return self.branch_at_scene(
            source_universe_id=source_universe_id,
            scene_id=scene_id,
            new_universe_id=new_universe_id,
            new_universe_name=new_universe_name,
            force=force,
            dry_run=dry_run,
        )
