"""
Main brancher service using composition pattern.

This module provides the main brancher interface that composes
cloning and branching services.
"""

from __future__ import annotations

from typing import Any

from core.services.branching.universe_brancher import UniverseBrancher
from core.services.branching.universe_cloner import UniverseCloner


class BrancherService:
    """Main brancher service that composes cloning and branching operations."""

    def __init__(self, repo: Any):
        self.repo = repo
        self.cloner = UniverseCloner(repo)
        self.brancher = UniverseBrancher(repo)

    # Cloning operations
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
        return self.cloner.clone_full(
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
        return self.cloner.clone_subset(
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

    # Branching operations
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
        return self.brancher.branch_at_scene(
            source_universe_id=source_universe_id,
            scene_id=scene_id,
            new_universe_id=new_universe_id,
            new_universe_name=new_universe_name,
            force=force,
            dry_run=dry_run,
        )
