from __future__ import annotations

from typing import Any


class EntitiesQueries:
    def entities_in_scene(self, scene_id: str) -> list[dict[str, Any]]:
        return self._rows(
            """
            MATCH (e:Entity)-[:APPEARS_IN]->(s:Scene {id:$sid})
            RETURN e.id AS id, e.name AS name, e.type AS type
            ORDER BY name
            """,
            sid=scene_id,
        )

    def entities_in_story(self, story_id: str) -> list[dict[str, Any]]:
        return self._rows(
            """
            MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
            MATCH (e:Entity)-[:APPEARS_IN]->(sc)
            RETURN DISTINCT e.id AS id, e.name AS name
            ORDER BY name
            """,
            sid=story_id,
        )

    def entities_in_universe(self, universe_id: str) -> list[dict[str, Any]]:
        return self._rows(
            """
            MATCH (u:Universe {id:$uid})-[:HAS_STORY]->(st:Story)
            MATCH (st)-[:HAS_SCENE]->(sc:Scene)
            MATCH (e:Entity)-[:APPEARS_IN]->(sc)
            RETURN DISTINCT e.id AS id, e.name AS name
            ORDER BY name
            """,
            uid=universe_id,
        )

    def entities_in_arc(self, arc_id: str) -> list[dict[str, Any]]:
        return self._rows(
            """
            MATCH (a:Arc {id:$aid})-[:HAS_STORY]->(st:Story)
            MATCH (st)-[:HAS_SCENE]->(sc:Scene)
            MATCH (e:Entity)-[:APPEARS_IN]->(sc)
            RETURN DISTINCT e.id AS id, e.name AS name
            ORDER BY name
            """,
            aid=arc_id,
        )

    def entities_in_story_by_role(self, story_id: str, role: str) -> list[dict[str, Any]]:
        return self._rows(
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

    def entities_in_arc_by_role(self, arc_id: str, role: str) -> list[dict[str, Any]]:
        return self._rows(
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

    def entities_in_universe_by_role(self, universe_id: str, role: str) -> list[dict[str, Any]]:
        return self._rows(
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
