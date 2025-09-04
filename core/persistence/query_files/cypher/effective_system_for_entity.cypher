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
