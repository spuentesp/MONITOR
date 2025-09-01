from __future__ import annotations

from typing import Any, Dict, List


class ScenesQueries:
    def scenes_for_entity(self, entity_id: str) -> List[Dict[str, Any]]:
        return self._rows(
            """
            MATCH (e:Entity {id:$eid})-[:APPEARS_IN]->(sc:Scene)
            OPTIONAL MATCH (st:Story)-[:HAS_SCENE]->(sc)
            RETURN sc.id AS scene_id, st.id AS story_id, sc.sequence_index AS sequence_index
            ORDER BY story_id, sequence_index
            """,
            eid=entity_id,
        )

    def participants_by_role_for_scene(self, scene_id: str) -> List[Dict[str, Any]]:
        return self._rows(
            """
            MATCH (f:Fact)-[:OCCURS_IN]->(s:Scene {id:$sid})
            MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
            WITH p.role AS role, collect(DISTINCT e.id) AS entities
            RETURN role, entities
            ORDER BY role
            """,
            sid=scene_id,
        )

    def participants_by_role_for_story(self, story_id: str) -> List[Dict[str, Any]]:
        return self._rows(
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

    def next_scene_for_entity_in_story(
        self, story_id: str, entity_id: str, after_sequence_index: int
    ) -> Dict[str, Any] | None:
        rows = self._rows(
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
        return rows[0] if rows else None

    def previous_scene_for_entity_in_story(
        self, story_id: str, entity_id: str, before_sequence_index: int
    ) -> Dict[str, Any] | None:
        rows = self._rows(
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
        return rows[0] if rows else None
