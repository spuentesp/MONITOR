from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.persistence.neo4j_repo import Neo4jRepo


class QueryService:
    def __init__(self, repo: Neo4jRepo):
        self.repo = repo

    def entities_in_scene(self, scene_id: str) -> List[Dict[str, Any]]:
        rows = self.repo.run(
            """
            MATCH (e:Entity)-[:APPEARS_IN]->(s:Scene {id:$sid})
            RETURN e.id AS id, e.name AS name, e.type AS type
            ORDER BY name
            """,
            sid=scene_id,
        )
        return [dict(r) for r in rows]

    def entities_in_story(self, story_id: str) -> List[Dict[str, Any]]:
        rows = self.repo.run(
            """
            MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
            MATCH (e:Entity)-[:APPEARS_IN]->(sc)
            RETURN DISTINCT e.id AS id, e.name AS name
            ORDER BY name
            """,
            sid=story_id,
        )
        return [dict(r) for r in rows]

    def facts_for_scene(self, scene_id: str) -> List[Dict[str, Any]]:
        rows = self.repo.run(
            """
            MATCH (f:Fact)-[:OCCURS_IN]->(s:Scene {id:$sid})
            OPTIONAL MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
            WITH f, collect({entity_id:e.id, role:p.role}) AS participants
            RETURN f.id AS id, f.description AS description, participants
            ORDER BY id
            """,
            sid=scene_id,
        )
        return [dict(r) for r in rows]

    def relation_state_history(self, entity_a: str, entity_b: str) -> List[Dict[str, Any]]:
        rows = self.repo.run(
            """
            MATCH (rs:RelationState)-[:REL_STATE_FOR {endpoint:'A'}]->(a:Entity {id:$a})
            MATCH (rs)-[:REL_STATE_FOR {endpoint:'B'}]->(b:Entity {id:$b})
            OPTIONAL MATCH (rs)-[:SET_IN_SCENE]->(s1:Scene)
            OPTIONAL MATCH (rs)-[:CHANGED_IN_SCENE]->(s2:Scene)
            OPTIONAL MATCH (rs)-[:ENDED_IN_SCENE]->(s3:Scene)
            RETURN rs.id AS id, rs.type AS type,
                   rs.started_at AS started_at, rs.ended_at AS ended_at,
                   s1.id AS set_in_scene, s2.id AS changed_in_scene, s3.id AS ended_in_scene
            ORDER BY started_at
            """,
            a=entity_a,
            b=entity_b,
        )
        return [dict(r) for r in rows]

    def axioms_applying_to_universe(self, universe_id: str) -> List[Dict[str, Any]]:
        rows = self.repo.run(
            """
            MATCH (a:Axiom)-[:APPLIES_TO]->(u:Universe {id:$uid})
            OPTIONAL MATCH (a)-[:REFERS_TO]->(ar:Archetype)
            RETURN a.id AS id, a.type AS type, a.semantics AS semantics, ar.id AS refers_to_archetype
            ORDER BY id
            """,
            uid=universe_id,
        )
        return [dict(r) for r in rows]

    def scenes_for_entity(self, entity_id: str) -> List[Dict[str, Any]]:
        rows = self.repo.run(
            """
            MATCH (e:Entity {id:$eid})-[:APPEARS_IN]->(sc:Scene)
            OPTIONAL MATCH (st:Story)-[:HAS_SCENE]->(sc)
            RETURN sc.id AS scene_id, st.id AS story_id, sc.sequence_index AS sequence_index
            ORDER BY story_id, sequence_index
            """,
            eid=entity_id,
        )
        return [dict(r) for r in rows]
