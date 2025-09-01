from __future__ import annotations

from core.domain.fact import Fact, RelationState


class FactsRelationsMixin:
    def _upsert_facts(self, universe_id: str, facts: list[Fact]):
        frows = []
        for f in facts:
            props = {
                "universe_id": universe_id,
                "description": f.description,
                "when": f.when,
                "time_span": f.time_span,
                "confidence": f.confidence,
                "derived_from": f.derived_from,
            }
            props = {k: self._sanitize(v) for k, v in props.items()}
            frows.append(
                {
                    "id": f.id,
                    "props": props,
                    "occurs_in": f.occurs_in,
                    "participants": [
                        {"entity_id": p.entity_id, "role": p.role} for p in f.participants
                    ],
                }
            )
        if not frows:
            return
        # Upsert facts and OCCURS_IN
        self.repo.run(
            """
            UNWIND $rows AS row
            MERGE (f:Fact {id: row.id})
            SET f += row.props
            WITH row, f
            OPTIONAL MATCH (sc:Scene {id: row.occurs_in})
            FOREACH (_ IN CASE WHEN sc IS NULL THEN [] ELSE [1] END | MERGE (f)-[:OCCURS_IN]->(sc))
            """,
            rows=frows,
        )
        # PARTICIPATES_AS
        self.repo.run(
            """
            UNWIND $rows AS row
            MATCH (f:Fact {id: row.id})
            UNWIND row.participants AS p
            MATCH (e:Entity {id: p.entity_id})
            MERGE (e)-[:PARTICIPATES_AS {role: p.role}]->(f)
            """,
            rows=frows,
        )

    def _upsert_relation_states(self, rels: list[RelationState]):
        rrows = [
            {
                "id": r.id,
                "props": {"type": r.type, "started_at": r.started_at, "ended_at": r.ended_at},
                "a": r.entity_a,
                "b": r.entity_b,
                "set": r.set_in_scene,
                "chg": r.changed_in_scene,
                "end": r.ended_in_scene,
            }
            for r in rels
        ]
        if not rrows:
            return
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
            rows=rrows,
        )
