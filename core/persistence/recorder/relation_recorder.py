"""Relationship persistence operations."""

from __future__ import annotations

from typing import Any

from .utils import ensure_id, sanitize_value


class RelationRecorder:
    """Handle relationship state and simple relation persistence."""

    def __init__(self, repo: Any):
        self.repo = repo

    def create_relation_states(
        self, relation_states: list[dict[str, Any]], scene_id: str | None
    ) -> tuple[int, list[str]]:
        """Create relation states with scene provenance. Returns (count, warnings)."""
        rows = []
        warnings: list[str] = []

        for r in relation_states:
            # Canonical ID for dedupe when not provided
            rid = r.get("id")
            if not rid and r.get("type") and r.get("entity_a") and r.get("entity_b"):
                rid = f"relstate:{r.get('type')}:{r.get('entity_a')}:{r.get('entity_b')}"
            rid = ensure_id("relstate", rid)
            rows.append(
                {
                    "id": rid,
                    "props": {
                        "type": r.get("type"),
                        "started_at": r.get("started_at"),
                        "ended_at": r.get("ended_at"),
                    },
                    "a": r.get("entity_a"),
                    "b": r.get("entity_b"),
                    "set": r.get("set_in_scene") or scene_id
                    if r.get("set_in_scene") is not None
                    else None,
                    "chg": r.get("changed_in_scene"),
                    "end": r.get("ended_in_scene"),
                }
            )
            if not (
                r.get("set_in_scene")
                or r.get("changed_in_scene")
                or r.get("ended_in_scene")
                or scene_id
            ):
                warnings.append(
                    f"RelationState {rid} has no provenance scene (set/changed/ended) and no default scene_id"
                )

        self.repo.run(
            """
            UNWIND $rows AS row
            MERGE (rs:RelationState {id: row.id})
            SET rs += row.props
            WITH rs, row
            MATCH (a:Entity {id: row.a})
            MATCH (b:Entity {id: row.b})
            MERGE (rs)-[:REL_STATE_FOR {endpoint:'A'}]->(a)
            MERGE (rs)-[:REL_STATE_FOR {endpoint:'B'}]->(b)
            WITH rs, row
            OPTIONAL MATCH (s1:Scene {id: row.set})
            FOREACH (_ IN CASE WHEN s1 IS NULL THEN [] ELSE [1] END | MERGE (rs)-[:SET_IN_SCENE]->(s1))
            WITH rs, row
            OPTIONAL MATCH (s2:Scene {id: row.chg})
            FOREACH (_ IN CASE WHEN s2 IS NULL THEN [] ELSE [1] END | MERGE (rs)-[:CHANGED_IN_SCENE]->(s2))
            WITH rs, row
            OPTIONAL MATCH (s3:Scene {id: row.end})
            FOREACH (_ IN CASE WHEN s3 IS NULL THEN [] ELSE [1] END | MERGE (rs)-[:ENDED_IN_SCENE]->(s3))
            """,
            rows=rows,
        )

        return len(rows), warnings

    def create_simple_relations(self, relations: list[dict[str, Any]]) -> int:
        """Create simple Entity-[:REL]->Entity relationships."""
        rrows = []
        for rel in relations:
            rrows.append(
                {
                    "a": rel.get("from") or rel.get("a"),
                    "b": rel.get("to") or rel.get("b"),
                    "type": rel.get("type"),
                    "weight": rel.get("weight"),
                    "temporal": sanitize_value(
                        rel.get("temporal")
                    ),  # {started_at, ended_at} optional
                }
            )

        self.repo.run(
            """
            UNWIND $rows AS row
            MATCH (a:Entity {id: row.a})
            MATCH (b:Entity {id: row.b})
            MERGE (a)-[r:REL {type: row.type}]->(b)
            SET r.weight = coalesce(row.weight, r.weight),
                r.temporal = coalesce(row.temporal, r.temporal)
            """,
            rows=rrows,
        )

        return len(rrows)
