from __future__ import annotations

from typing import Any, Dict, List


class SystemsQueries:
    def system_usage_summary(self, universe_id: str) -> List[Dict[str, Any]]:
        return self._rows(
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
