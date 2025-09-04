"""
Universe branching operations.

This module provides services for creating branches from existing universes.
"""

from __future__ import annotations

from typing import Any


class UniverseBrancher:
    """Handles universe branching operations."""
    
    def __init__(self, repo: Any):
        self.repo = repo
    
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
        # Validation
        self._check_source_and_target(source_universe_id, new_universe_id, force)
        
        # Check if scene exists in source universe
        scene_exists = self.repo.run(
            "MATCH (sc:Scene {id: $scene_id, universe_id: $src}) RETURN count(sc) > 0 AS exists",
            scene_id=scene_id,
            src=source_universe_id,
        )
        if not (scene_exists and scene_exists[0].get("exists", False)):
            raise ValueError(f"Scene {scene_id} not found in source universe {source_universe_id}")
        
        if dry_run:
            # Count operations that would be performed
            scenes_before = self._first_count(
                self.repo.run(
                    """
                    MATCH (sc:Scene {universe_id: $src})
                    WHERE sc.index <= (
                        SELECT s.index FROM Scene s WHERE s.id = $scene_id AND s.universe_id = $src
                    )
                    RETURN count(sc) AS c
                    """,
                    src=source_universe_id,
                    scene_id=scene_id,
                )
            )
            
            return {
                "dry_run": True,
                "branch_point": scene_id,
                "operations": {
                    "scenes_included": scenes_before,
                },
            }
        
        # Execute branch operation
        result: dict[str, Any] = {"branched": True, "branch_point": scene_id, "operations": []}
        
        # Create new universe
        self.repo.run(
            """
            MATCH (src:Universe {id: $src})
            CREATE (branch:Universe {
                id: $branch_id,
                name: COALESCE($name, src.name + ' (Branch)'),
                description: src.description,
                created_at: datetime(),
                branched_from: $src,
                branch_scene: $scene_id
            })
            """,
            src=source_universe_id,
            branch_id=new_universe_id,
            name=new_universe_name,
            scene_id=scene_id,
        )
        result["operations"].append("universe")
        
        # Copy all content up to and including the branch scene
        self.repo.run(
            """
            MATCH (src:Universe {id: $src})
            MATCH (branch:Universe {id: $branch_id})
            MATCH (sc:Scene {universe_id: $src})
            WHERE sc.index <= (
                SELECT s.index FROM Scene s WHERE s.id = $scene_id AND s.universe_id = $src
            )
            CREATE (new_sc:Scene {
                id: $branch_id + '_scene_' + sc.id,
                universe_id: $branch_id,
                index: sc.index,
                title: sc.title,
                description: sc.description,
                created_at: datetime()
            })
            """,
            src=source_universe_id,
            branch_id=new_universe_id,
            scene_id=scene_id,
        )
        result["operations"].append("scenes")
        
        return result
    
    def _check_source_and_target(
        self, source_universe_id: str, new_universe_id: str, force: bool
    ) -> None:
        """Check source exists and target constraints."""
        rows = self.repo.run(
            """
            OPTIONAL MATCH (src:Universe {id:$src})
            OPTIONAL MATCH (tgt:Universe {id:$tgt})
            RETURN src IS NOT NULL AS src_ok, tgt IS NOT NULL AS tgt_exists
            """,
            src=source_universe_id,
            tgt=new_universe_id,
        )
        src_ok = rows and rows[0].get("src_ok", False)
        tgt_exists = rows and rows[0].get("tgt_exists", False)
        if not src_ok:
            raise ValueError("Source universe not found")
        if tgt_exists and not force:
            raise ValueError(
                "Target universe already exists; use --force to overwrite or choose a new id"
            )
    
    @staticmethod
    def _first_count(rows: list[dict[str, Any]] | list[Any]) -> int:
        """Extract count from first row."""
        return int(rows[0]["c"]) if rows and "c" in rows[0] else 0
