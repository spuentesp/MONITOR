from __future__ import annotations

from typing import Any, Dict, List

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

    def entities_in_universe(self, universe_id: str) -> List[Dict[str, Any]]:
        rows = self.repo.run(
            """
            MATCH (u:Universe {id:$uid})-[:HAS_STORY]->(st:Story)
            MATCH (st)-[:HAS_SCENE]->(sc:Scene)
            MATCH (e:Entity)-[:APPEARS_IN]->(sc)
            RETURN DISTINCT e.id AS id, e.name AS name
            ORDER BY name
            """,
            uid=universe_id,
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

    def entities_in_arc(self, arc_id: str) -> List[Dict[str, Any]]:
        rows = self.repo.run(
            """
            MATCH (a:Arc {id:$aid})-[:HAS_STORY]->(st:Story)
            MATCH (st)-[:HAS_SCENE]->(sc:Scene)
            MATCH (e:Entity)-[:APPEARS_IN]->(sc)
            RETURN DISTINCT e.id AS id, e.name AS name
            ORDER BY name
            """,
            aid=arc_id,
        )
        return [dict(r) for r in rows]

    def entities_in_story_by_role(self, story_id: str, role: str) -> List[Dict[str, Any]]:
        rows = self.repo.run(
            """
            MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
            MATCH (f:Fact)-[:OCCURS_IN]->(sc)
            MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
            WHERE p.role = $role
            RETURN DISTINCT e.id AS id, e.name AS name
            ORDER BY name
            """,
            sid=story_id,
            role=role,
        )
        return [dict(r) for r in rows]

    def entities_in_arc_by_role(self, arc_id: str, role: str) -> List[Dict[str, Any]]:
        rows = self.repo.run(
            """
            MATCH (a:Arc {id:$aid})-[:HAS_STORY]->(st:Story)
            MATCH (st)-[:HAS_SCENE]->(sc:Scene)
            MATCH (f:Fact)-[:OCCURS_IN]->(sc)
            MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
            WHERE p.role = $role
            RETURN DISTINCT e.id AS id, e.name AS name
            ORDER BY name
            """,
            aid=arc_id,
            role=role,
        )
        return [dict(r) for r in rows]

    def entities_in_universe_by_role(self, universe_id: str, role: str) -> List[Dict[str, Any]]:
        rows = self.repo.run(
            """
            MATCH (u:Universe {id:$uid})-[:HAS_STORY]->(st:Story)
            MATCH (st)-[:HAS_SCENE]->(sc:Scene)
            MATCH (f:Fact)-[:OCCURS_IN]->(sc)
            MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
            WHERE p.role = $role
            RETURN DISTINCT e.id AS id, e.name AS name
            ORDER BY name
            """,
            uid=universe_id,
            role=role,
        )
        return [dict(r) for r in rows]

    def facts_for_story(self, story_id: str) -> List[Dict[str, Any]]:
        rows = self.repo.run(
            """
            MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
            MATCH (f:Fact)-[:OCCURS_IN]->(sc)
            OPTIONAL MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
            WITH f, collect({entity_id:e.id, role:p.role}) AS participants
            RETURN f.id AS id, f.description AS description, participants
            ORDER BY id
            """,
            sid=story_id,
        )
        return [dict(r) for r in rows]

    def participants_by_role_for_scene(self, scene_id: str) -> List[Dict[str, Any]]:
        rows = self.repo.run(
            """
            MATCH (f:Fact)-[:OCCURS_IN]->(s:Scene {id:$sid})
            MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
            WITH p.role AS role, collect(DISTINCT e.id) AS entities
            RETURN role, entities
            ORDER BY role
            """,
            sid=scene_id,
        )
        return [dict(r) for r in rows]

    def participants_by_role_for_story(self, story_id: str) -> List[Dict[str, Any]]:
        rows = self.repo.run(
            """
            MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
            MATCH (f:Fact)-[:OCCURS_IN]->(sc)
            MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
            WITH p.role AS role, collect(DISTINCT e.id) AS entities
            RETURN role, entities
            ORDER BY role
            """,
            sid=story_id,
        )
        return [dict(r) for r in rows]

    def system_usage_summary(self, universe_id: str) -> List[Dict[str, Any]]:
        rows = self.repo.run(
            """
            MATCH (u:Universe {id:$uid})
            CALL {
              WITH u
              MATCH (u)-[:USES_SYSTEM]->(sys:System)
              RETURN sys.id AS sid, 'universe' AS kind, count(*) AS c
            }
            UNION ALL
            CALL {
              WITH u
              MATCH (u)-[:HAS_STORY]->(:Story)-[:USES_SYSTEM]->(sys:System)
              RETURN sys.id AS sid, 'story' AS kind, count(*) AS c
            }
            UNION ALL
            CALL {
              WITH u
              MATCH (e:Entity)-[:BELONGS_TO]->(u)
              MATCH (e)-[:USES_SYSTEM]->(sys:System)
              RETURN sys.id AS sid, 'entity' AS kind, count(*) AS c
            }
            UNION ALL
            CALL {
              WITH u
              MATCH (e:Entity)-[:BELONGS_TO]->(u)
              MATCH (e)-[:HAS_SHEET]->(:Sheet)-[:USES_SYSTEM]->(sys:System)
              RETURN sys.id AS sid, 'sheet' AS kind, count(*) AS c
            }
            RETURN sid AS system_id,
                   sum(CASE WHEN kind='universe' THEN c ELSE 0 END) AS universe_count,
                   sum(CASE WHEN kind='story' THEN c ELSE 0 END) AS story_count,
                   sum(CASE WHEN kind='entity' THEN c ELSE 0 END) AS entity_count,
                   sum(CASE WHEN kind='sheet' THEN c ELSE 0 END) AS sheet_count
            ORDER BY system_id
            """,
            uid=universe_id,
        )
        return [dict(r) for r in rows]

    def axioms_effective_in_scene(self, scene_id: str) -> List[Dict[str, Any]]:
        rows = self.repo.run(
            """
            MATCH (st:Story)-[:HAS_SCENE]->(sc:Scene {id:$sid})
            MATCH (u:Universe)-[:HAS_STORY]->(st)
            MATCH (a:Axiom)-[:APPLIES_TO]->(u)
            OPTIONAL MATCH (a)-[:REFERS_TO]->(ar:Archetype)
            RETURN a.id AS id, a.type AS type, a.semantics AS semantics, ar.id AS refers_to_archetype
            ORDER BY id
            """,
            sid=scene_id,
        )
        return [dict(r) for r in rows]

    def next_scene_for_entity_in_story(self, story_id: str, entity_id: str, after_sequence_index: int) -> Dict[str, Any] | None:
        rows = self.repo.run(
            """
            MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
            WHERE sc.sequence_index > $idx
            MATCH (e:Entity {id:$eid})-[:APPEARS_IN]->(sc)
            RETURN sc.id AS scene_id, sc.sequence_index AS sequence_index
            ORDER BY sequence_index ASC
            LIMIT 1
            """,
            sid=story_id,
            eid=entity_id,
            idx=after_sequence_index,
        )
        return dict(rows[0]) if rows else None

    def previous_scene_for_entity_in_story(self, story_id: str, entity_id: str, before_sequence_index: int) -> Dict[str, Any] | None:
        rows = self.repo.run(
            """
            MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
            WHERE sc.sequence_index < $idx
            MATCH (e:Entity {id:$eid})-[:APPEARS_IN]->(sc)
            RETURN sc.id AS scene_id, sc.sequence_index AS sequence_index
            ORDER BY sequence_index DESC
            LIMIT 1
            """,
            sid=story_id,
            eid=entity_id,
            idx=before_sequence_index,
        )
        return dict(rows[0]) if rows else None
