"""Scene persistence operations."""

from __future__ import annotations

from typing import Any

from .utils import ensure_id, sanitize_value


class SceneRecorder:
    """Handle scene creation, linking, and participant management."""

    def __init__(self, repo: Any):
        self.repo = repo

    def create_scene(self, new_scene: dict[str, Any]) -> tuple[str, int, list[str]]:
        """Create scene and manage participants. Returns (scene_id, appears_in_count, warnings)."""
        sc_id = ensure_id("scene", new_scene.get("id"))
        props = {
            "story_id": new_scene.get("story_id"),
            "sequence_index": new_scene.get("sequence_index"),
            "when": new_scene.get("when"),
            "time_span": sanitize_value(new_scene.get("time_span")),
            "recorded_at": new_scene.get("recorded_at"),
            "location": new_scene.get("location"),
        }
        
        self.repo.run(
            """
            UNWIND [$row] AS row
            MERGE (sc:Scene {id: row.id})
            SET sc.story_id = row.props.story_id,
                sc.sequence_index = row.props.sequence_index,
                sc.when = row.props.when,
                sc.time_span = row.props.time_span,
                sc.recorded_at = row.props.recorded_at,
                sc.location = row.props.location
            WITH sc, row
            CALL {
              WITH sc, row
              WITH sc, row WHERE row.props.story_id IS NOT NULL
              MATCH (st:Story {id: row.props.story_id})
              MERGE (st)-[hs:HAS_SCENE]->(sc)
              FOREACH (_ IN CASE WHEN row.props.sequence_index IS NULL THEN [] ELSE [1] END | SET hs.sequence_index = row.props.sequence_index)
            }
            RETURN sc
            """,
            row={"id": sc_id, "props": props},
        )
        
        # Handle participants
        participants = new_scene.get("participants") or []
        appears_in_count = 0
        warnings: list[str] = []
        
        if participants:
            self.repo.run(
                """
                UNWIND $rows AS row
                MATCH (sc:Scene {id: $sid})
                MATCH (e:Entity {id: row.eid})
                MERGE (e)-[:APPEARS_IN]->(sc)
                """,
                rows=[{"eid": eid} for eid in participants],
                sid=sc_id,
            )
            appears_in_count = len(participants)
            
            # Optional DB existence check for participants
            try:
                if hasattr(self.repo, "ping") and self.repo.ping() and participants:
                    rows = self.repo.run(
                        "MATCH (e:Entity) WHERE e.id IN $ids RETURN collect(e.id) AS ids",
                        ids=participants,
                    )
                    present = set((rows[0]["ids"] if rows else []) or [])
                    missing = [x for x in participants if x not in present]
                    if missing:
                        warnings.append(f"APPEARS_IN skipped for missing entities: {missing}")
            except Exception:
                # Never fail commit for warning checks
                pass
                
        return sc_id, appears_in_count, warnings
