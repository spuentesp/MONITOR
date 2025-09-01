from __future__ import annotations

from typing import Any, Dict, List


class RelationsQueries:
    def relation_state_history(self, entity_a: str, entity_b: str) -> List[Dict[str, Any]]:
        return self._rows(
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
