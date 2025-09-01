from __future__ import annotations

from typing import Any, Dict, List


class SystemsQueries:
    def system_usage_summary(self, universe_id: str) -> List[Dict[str, Any]]:
        return self._rows(
            """
            CALL {
              MATCH (u:Universe {id:$uid})-[:USES_SYSTEM]->(sys:System)
              RETURN sys.id AS sid, 'universe' AS kind, count(*) AS c
              UNION ALL
              MATCH (u:Universe {id:$uid})-[:HAS_STORY]->(:Story)-[:USES_SYSTEM]->(sys:System)
              RETURN sys.id AS sid, 'story' AS kind, count(*) AS c
              UNION ALL
              MATCH (u:Universe {id:$uid})<-[:BELONGS_TO]-(e:Entity)
              MATCH (e)-[:USES_SYSTEM]->(sys:System)
              RETURN sys.id AS sid, 'entity' AS kind, count(*) AS c
              UNION ALL
              MATCH (u:Universe {id:$uid})<-[:BELONGS_TO]-(e:Entity)
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

    def effective_system_for_universe(self, universe_id: str) -> Dict[str, Any] | None:
     rows = self._rows(
      """
      MATCH (u:Universe {id:$uid})
      OPTIONAL MATCH (u)-[:USES_SYSTEM]->(su:System)
      OPTIONAL MATCH (m:Multiverse)-[:HAS_UNIVERSE]->(u)
      OPTIONAL MATCH (m)-[:USES_SYSTEM]->(sm:System)
      WITH su, sm,
        CASE WHEN su IS NOT NULL THEN 'universe'
          WHEN sm IS NOT NULL THEN 'multiverse'
        END AS source
      RETURN coalesce(su.id, sm.id) AS system_id, source
      """,
      uid=universe_id,
     )
     return rows[0] if rows else None

    def effective_system_for_story(self, story_id: str) -> Dict[str, Any] | None:
     rows = self._rows(
      """
      MATCH (st:Story {id:$sid})
      OPTIONAL MATCH (st)-[:USES_SYSTEM]->(ss:System)
      OPTIONAL MATCH (u:Universe)-[:HAS_STORY]->(st)
      OPTIONAL MATCH (u)-[:USES_SYSTEM]->(su:System)
      OPTIONAL MATCH (m:Multiverse)-[:HAS_UNIVERSE]->(u)
      OPTIONAL MATCH (m)-[:USES_SYSTEM]->(sm:System)
      WITH ss, su, sm,
        CASE WHEN ss IS NOT NULL THEN 'story'
          WHEN su IS NOT NULL THEN 'universe'
          WHEN sm IS NOT NULL THEN 'multiverse'
        END AS source
      RETURN coalesce(ss.id, su.id, sm.id) AS system_id, source
      """,
      sid=story_id,
     )
     return rows[0] if rows else None

    def effective_system_for_scene(self, scene_id: str) -> Dict[str, Any] | None:
     rows = self._rows(
      """
      MATCH (st:Story)-[:HAS_SCENE]->(sc:Scene {id:$sid})
      OPTIONAL MATCH (st)-[:USES_SYSTEM]->(ss:System)
      OPTIONAL MATCH (u:Universe)-[:HAS_STORY]->(st)
      OPTIONAL MATCH (u)-[:USES_SYSTEM]->(su:System)
      OPTIONAL MATCH (m:Multiverse)-[:HAS_UNIVERSE]->(u)
      OPTIONAL MATCH (m)-[:USES_SYSTEM]->(sm:System)
      WITH ss, su, sm,
        CASE WHEN ss IS NOT NULL THEN 'story'
          WHEN su IS NOT NULL THEN 'universe'
          WHEN sm IS NOT NULL THEN 'multiverse'
        END AS source
      RETURN coalesce(ss.id, su.id, sm.id) AS system_id, source
      """,
      sid=scene_id,
     )
     return rows[0] if rows else None

    def effective_system_for_entity(self, entity_id: str) -> Dict[str, Any] | None:
     rows = self._rows(
      """
      MATCH (e:Entity {id:$eid})
      OPTIONAL MATCH (e)-[:USES_SYSTEM]->(se:System)
      // Gather sheet systems (if any)
      OPTIONAL MATCH (e)-[:HAS_SHEET]->(:Sheet)-[:USES_SYSTEM]->(ss:System)
      WITH se, collect(ss.id) AS sheet_ids
      WITH se, sheet_ids,
        CASE WHEN size(sheet_ids) = 0 THEN NULL ELSE sheet_ids[0] END AS sheet_choice
      WITH coalesce(se.id, sheet_choice) AS sid,
        CASE WHEN se IS NOT NULL THEN 'entity'
          WHEN size(sheet_ids) > 0 THEN 'sheet'
        END AS source
      RETURN sid AS system_id, source
      """,
      eid=entity_id,
     )
     return rows[0] if rows else None

    def effective_system_for_entity_in_story(self, entity_id: str, story_id: str) -> Dict[str, Any] | None:
     rows = self._rows(
      """
      MATCH (e:Entity {id:$eid})
      MATCH (st:Story {id:$sid})
      OPTIONAL MATCH (e)-[:USES_SYSTEM]->(se:System)
      // Prefer sheets scoped to this story if present, else any sheet
      OPTIONAL MATCH (e)-[hs:HAS_SHEET]->(sh:Sheet)
      OPTIONAL MATCH (sh)-[:USES_SYSTEM]->(ss:System)
      WITH e, st, se,
        [s IN collect({sid: ss.id, story_id: hs.story_id}) WHERE s.sid IS NOT NULL] AS sheet_pairs
      WITH se, st,
        // filter by matching story_id first
        [sp IN sheet_pairs WHERE sp.story_id = st.id AND sp.sid IS NOT NULL][0].sid AS sh_story_sid,
        CASE WHEN size(sheet_pairs) = 0 THEN NULL ELSE sheet_pairs[0].sid END AS sh_any_sid
      // Fallback to story/universe/multiverse scope if no entity/sheet system
      OPTIONAL MATCH (st)-[:USES_SYSTEM]->(ss_st:System)
      OPTIONAL MATCH (u:Universe)-[:HAS_STORY]->(st)
      OPTIONAL MATCH (u)-[:USES_SYSTEM]->(su:System)
      OPTIONAL MATCH (m:Multiverse)-[:HAS_UNIVERSE]->(u)
      OPTIONAL MATCH (m)-[:USES_SYSTEM]->(sm:System)
      WITH se, sh_story_sid, sh_any_sid, ss_st, su, sm,
        CASE
          WHEN se IS NOT NULL THEN 'entity'
          WHEN sh_story_sid IS NOT NULL THEN 'sheet@story'
          WHEN sh_any_sid IS NOT NULL THEN 'sheet'
          WHEN ss_st IS NOT NULL THEN 'story'
          WHEN su IS NOT NULL THEN 'universe'
          WHEN sm IS NOT NULL THEN 'multiverse'
        END AS source,
        coalesce(se.id, sh_story_sid, sh_any_sid, ss_st.id, su.id, sm.id) AS sid
      RETURN sid AS system_id, source
      """,
      eid=entity_id,
      sid=story_id,
     )
     return rows[0] if rows else None
