from __future__ import annotations

from typing import Any


class AxiomsQueries:
    def axioms_applying_to_universe(self, universe_id: str) -> list[dict[str, Any]]:
        return self._rows(
            """
            MATCH (a:Axiom)-[:APPLIES_TO]->(u:Universe {id:$uid})
            OPTIONAL MATCH (a)-[:REFERS_TO]->(ar:Archetype)
            RETURN a.id AS id, a.type AS type, a.semantics AS semantics, ar.id AS refers_to_archetype
            ORDER BY id
            """,
            uid=universe_id,
        )

    def axioms_effective_in_scene(self, scene_id: str) -> list[dict[str, Any]]:
        return self._rows(
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
