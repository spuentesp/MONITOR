from __future__ import annotations

from typing import Any


class FactsQueries:
    def facts_for_scene(self, scene_id: str) -> list[dict[str, Any]]:
        return self._rows(
            """
            MATCH (f:Fact)-[:OCCURS_IN]->(s:Scene {id:$sid})
            OPTIONAL MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
            WITH f, collect({entity_id:e.id, role:p.role}) AS participants
            RETURN f.id AS id, f.description AS description, participants
            ORDER BY id
            """,
            sid=scene_id,
        )

    def facts_for_story(self, story_id: str) -> list[dict[str, Any]]:
        return self._rows(
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
