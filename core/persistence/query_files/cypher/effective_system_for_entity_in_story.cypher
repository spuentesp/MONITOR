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
