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
