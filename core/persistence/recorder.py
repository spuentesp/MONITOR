from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

try:
    from core.ports.storage import RepoPort  # type: ignore
except Exception:  # pragma: no cover
    RepoPort = Any  # type: ignore

from core.persistence.neo4j_repo import Neo4jRepo


class RecorderService:
    """Persist Facts and RelationState deltas to the graph.

    Note: Canonical policy remains YAML-first; use this for dev or controlled autopilot flows.
    """

    def __init__(self, repo: RepoPort | Neo4jRepo):
        self.repo = repo

    @staticmethod
    def _ensure_id(prefix: str, id_: str | None) -> str:
        return id_ or f"{prefix}:{uuid4()}"

    @staticmethod
    def _is_primitive(x: Any) -> bool:
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
            if not value:
                # Avoid empty Map{} (invalid in Neo4j); store as JSON string
                return json.dumps(value, ensure_ascii=False)
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def commit_deltas(
        self,
        *,
        scene_id: str | None = None,
        facts: list[dict[str, Any]] | None = None,
        relation_states: list[dict[str, Any]] | None = None,
        relations: list[dict[str, Any]] | None = None,
        universe_id: str | None = None,
        new_multiverse: dict[str, Any] | None = None,
        new_universe: dict[str, Any] | None = None,
        new_arc: dict[str, Any] | None = None,
        new_story: dict[str, Any] | None = None,
        new_scene: dict[str, Any] | None = None,
        new_entities: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        facts = facts or []
        relation_states = relation_states or []
        relations = relations or []
        new_entities = new_entities or []
        written = {
            "facts": 0,
            "relation_states": 0,
            "relations": 0,
            "entities": 0,
            "scenes": 0,
            "appears_in": 0,
            "stories": 0,
            "arcs": 0,
            "universes": 0,
            "multiverses": 0,
        }
        warnings: list[str] = []

        # Preflight: basic mismatch checks without DB I/O
        if (
            new_story
            and universe_id
            and new_story.get("universe_id")
            and new_story.get("universe_id") != universe_id
        ):
            warnings.append(
                f"new_story.universe_id ({new_story.get('universe_id')}) differs from provided universe_id ({universe_id})"
            )
        if (
            new_arc
            and universe_id
            and new_arc.get("universe_id")
            and new_arc.get("universe_id") != universe_id
        ):
            warnings.append(
                f"new_arc.universe_id ({new_arc.get('universe_id')}) differs from provided universe_id ({universe_id})"
            )
        if new_entities and universe_id:
            for e in new_entities:
                if e.get("universe_id") and e.get("universe_id") != universe_id:
                    warnings.append(
                        f"entity {e.get('id') or e.get('name')} universe_id ({e.get('universe_id')}) differs from provided universe_id ({universe_id})"
                    )

        # -2) Multiverse upsert and Omniverse link
        if new_multiverse:
            mv_id = self._ensure_id("multiverse", new_multiverse.get("id"))
            props = {
                "name": new_multiverse.get("name"),
                "description": new_multiverse.get("description"),
            }
            self.repo.run(
                """
                UNWIND [$row] AS row
                MERGE (m:Multiverse {id: row.id})
                SET m.name = row.props.name,
                    m.description = row.props.description
                WITH m, row
                OPTIONAL MATCH (o:Omniverse {id: row.omni})
                FOREACH (_ IN CASE WHEN o IS NULL THEN [] ELSE [1] END | MERGE (o)-[:HAS]->(m))
                """,
                row={"id": mv_id, "props": props, "omni": new_multiverse.get("omniverse_id")},
            )
            written["multiverses"] = 1

        # -1) Universe upsert and Multiverse link
        if new_universe:
            u_id = self._ensure_id("universe", new_universe.get("id"))
            props = {
                "name": new_universe.get("name"),
                "description": new_universe.get("description"),
            }
            self.repo.run(
                """
                UNWIND [$row] AS row
                MERGE (u:Universe {id: row.id})
                SET u.name = row.props.name,
                    u.description = row.props.description
                WITH u, row
                OPTIONAL MATCH (m:Multiverse {id: row.mv})
                FOREACH (_ IN CASE WHEN m IS NULL THEN [] ELSE [1] END | MERGE (m)-[:HAS_UNIVERSE]->(u))
                """,
                row={"id": u_id, "props": props, "mv": new_universe.get("multiverse_id")},
            )
            # set default universe_id for subsequent operations if not provided
            universe_id = universe_id or u_id
            written["universes"] = 1

        # 0a) Arc upsert and link to Universe
        if new_arc:
            if not (new_arc.get("universe_id") or universe_id):
                raise ValueError("universe_id is required to create arcs")
            a_id = self._ensure_id("arc", new_arc.get("id"))
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
            written["arcs"] = 1

        # 0b) Story upsert and link to Universe (and optionally Arc)
        if new_story:
            if not (new_story.get("universe_id") or universe_id):
                raise ValueError("universe_id is required to create stories")
            st_id = self._ensure_id("story", new_story.get("id"))
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
                FOREACH (_ IN CASE WHEN u IS NULL THEN [] ELSE [1] END | MERGE (u)-[:HAS_STORY {sequence_index: row.seq}]->(s))
                WITH s, row
                OPTIONAL MATCH (a:Arc {id: row.props.arc_id})
                FOREACH (_ IN CASE WHEN a IS NULL THEN [] ELSE [1] END | MERGE (a)-[:HAS_STORY {sequence_index: row.seq}]->(s))
                """,
                row={"id": st_id, "props": props, "seq": new_story.get("sequence_index")},
            )
            written["stories"] = 1

        # 0) Entities (PCs/NPCs) minimal upsert and BELONGS_TO
        if new_entities:
            if not universe_id:
                raise ValueError("universe_id is required to create entities")
            erows = []
            for e in new_entities:
                eid = self._ensure_id("entity", e.get("id"))
                erows.append(
                    {
                        "id": eid,
                        "name": e.get("name"),
                        "type": e.get("type"),
                        "universe_id": e.get("universe_id") or universe_id,
                        "attributes": self._sanitize(e.get("attributes") or {}),
                    }
                )
            self.repo.run(
                """
                UNWIND $rows AS row
                MERGE (e:Entity {id: row.id})
                SET e.name = row.name,
                    e.type = coalesce(row.type, e.type),
                    e.universe_id = row.universe_id,
                    e.attributes = row.attributes
                WITH e, row
                OPTIONAL MATCH (u:Universe {id: row.universe_id})
                FOREACH (_ IN CASE WHEN u IS NULL THEN [] ELSE [1] END | MERGE (e)-[:BELONGS_TO]->(u))
                """,
                rows=erows,
            )
            written["entities"] = len(erows)

        # 1) Scene upsert and optional Story link
        if new_scene:
            sc_id = self._ensure_id("scene", new_scene.get("id"))
            props = {
                "story_id": new_scene.get("story_id"),
                "sequence_index": new_scene.get("sequence_index"),
                "when": new_scene.get("when"),
                "time_span": self._sanitize(new_scene.get("time_span")),
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
            # Scene participants (APPEARS_IN)
            participants = new_scene.get("participants") or []
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
                written["appears_in"] = len(participants)
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
            written["scenes"] = 1
            # Set scene_id for subsequent facts/relation_states defaulting
            scene_id = scene_id or sc_id

        if facts:
            rows = []
            for f in facts:
                fid = self._ensure_id("fact", f.get("id"))
                props = {
                    "universe_id": f.get("universe_id") or universe_id,
                    "description": f.get("description"),
                    "when": f.get("when"),
                    "time_span": self._sanitize(f.get("time_span")),
                    "confidence": f.get("confidence"),
                    "derived_from": self._sanitize(f.get("derived_from")),
                }
                participants = f.get("participants", [])
                rows.append(
                    {
                        "id": fid,
                        "props": props,
                        "occurs_in": f.get("occurs_in") or scene_id,
                        "participants": participants,
                    }
                )
            self.repo.run(
                """
                UNWIND $rows AS row
                MERGE (f:Fact {id: row.id})
                SET f += row.props
                WITH row, f
                OPTIONAL MATCH (sc:Scene {id: row.occurs_in})
                FOREACH (_ IN CASE WHEN sc IS NULL THEN [] ELSE [1] END | MERGE (f)-[:OCCURS_IN]->(sc))
                """,
                rows=rows,
            )
            self.repo.run(
                """
                UNWIND $rows AS row
                MATCH (f:Fact {id: row.id})
                UNWIND row.participants AS p
                MATCH (e:Entity {id: p.entity_id})
                MERGE (e)-[:PARTICIPATES_AS {role: p.role}]->(f)
                """,
                rows=rows,
            )
            written["facts"] = len(rows)

        if relation_states:
            rows = []
            for r in relation_states:
                # Canonical ID for dedupe when not provided
                rid = r.get("id")
                if not rid and r.get("type") and r.get("entity_a") and r.get("entity_b"):
                    rid = f"relstate:{r.get('type')}:{r.get('entity_a')}:{r.get('entity_b')}"
                rid = self._ensure_id("relstate", rid)
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
            written["relation_states"] = len(rows)

        # 4) Simple Relations (Entity-[:REL]->Entity) — timeless or interval
        if relations:
            rrows = []
            for rel in relations:
                rrows.append(
                    {
                        "a": rel.get("from") or rel.get("a"),
                        "b": rel.get("to") or rel.get("b"),
                        "type": rel.get("type"),
                        "weight": rel.get("weight"),
                        "temporal": self._sanitize(
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
            written["relations"] = len(rrows)

        return {"ok": True, "written": written, "warnings": warnings}
