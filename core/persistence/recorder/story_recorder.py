"""Story and arc persistence operations."""

from __future__ import annotations

from typing import Any

from .utils import ensure_id


class StoryRecorder:
    """Handle story and arc creation and linking."""

    def __init__(self, repo: Any):
        self.repo = repo

    def create_arc(self, new_arc: dict[str, Any], universe_id: str) -> str:
        """Create arc and link to universe."""
        if not (new_arc.get("universe_id") or universe_id):
            raise ValueError("universe_id is required to create arcs")

        a_id = ensure_id("arc", new_arc.get("id"))
        self.repo.run(
            """
            UNWIND [$row] AS row
            MERGE (a:Arc {id: row.id})
            SET a.title = row.title,
                a.tags = coalesce(row.tags, a.tags),
                a.ordering_mode = coalesce(row.ordering_mode, a.ordering_mode),
                a.universe_id = row.universe_id
            WITH a, row
            OPTIONAL MATCH (u:Universe {id: row.universe_id})
            FOREACH (_ IN CASE WHEN u IS NULL THEN [] ELSE [1] END | MERGE (u)-[:HAS_ARC]->(a))
            """,
            row={
                "id": a_id,
                "title": new_arc.get("title"),
                "tags": new_arc.get("tags"),
                "ordering_mode": new_arc.get("ordering_mode"),
                "universe_id": new_arc.get("universe_id") or universe_id,
            },
        )
        return a_id

    def create_story(self, new_story: dict[str, Any], universe_id: str) -> str:
        """Create story and link to universe and optionally arc."""
        if not (new_story.get("universe_id") or universe_id):
            raise ValueError("universe_id is required to create stories")

        st_id = ensure_id("story", new_story.get("id"))
        u_for_story = new_story.get("universe_id") or universe_id
        props = {
            "title": new_story.get("title"),
            "summary": new_story.get("summary"),
            "universe_id": u_for_story,
            "arc_id": new_story.get("arc_id"),
        }
        self.repo.run(
            """
            UNWIND [$row] AS row
            MERGE (s:Story {id: row.id})
            SET s += row.props
            WITH s, row
            OPTIONAL MATCH (u:Universe {id: row.props.universe_id})
            FOREACH (_ IN CASE WHEN u IS NULL THEN [] ELSE [1] END | MERGE (u)-[r:HAS_STORY]->(s))
            WITH s, row, r
                            FOREACH (_ IN CASE WHEN row.seq IS NULL THEN [] ELSE [1] END | SET r.sequence_index = row.seq)
                            WITH s, row, r
                            CALL {
                                WITH row, r
                                WITH row, r WHERE row.seq IS NULL
                                MATCH (u2:Universe {id: row.props.universe_id})-[rs:HAS_STORY]->(:Story)
                                WITH r, coalesce(max(rs.sequence_index), -1) + 1 AS next_idx
                                SET r.sequence_index = coalesce(r.sequence_index, next_idx)
                                RETURN 0 AS _
                            }
            WITH s, row
            OPTIONAL MATCH (a:Arc {id: row.props.arc_id})
            FOREACH (_ IN CASE WHEN a IS NULL THEN [] ELSE [1] END | MERGE (a)-[ra:HAS_STORY]->(s))
            WITH s, row, ra
            FOREACH (_ IN CASE WHEN row.seq IS NULL THEN [] ELSE [1] END | SET ra.sequence_index = row.seq)
            """,
            row={"id": st_id, "props": props, "seq": new_story.get("sequence_index")},
        )
        return st_id
