-- Effective system for universe with inheritance hierarchy
-- Parameters: $uid (universe_id)
MATCH (u:Universe {id:$uid})
OPTIONAL MATCH (u)-[:USES_SYSTEM]->(su:System)
OPTIONAL MATCH (m:Multiverse)-[:HAS_UNIVERSE]->(u)
OPTIONAL MATCH (m)-[:USES_SYSTEM]->(sm:System)
WITH su, sm,
  CASE WHEN su IS NOT NULL THEN 'universe'
    WHEN sm IS NOT NULL THEN 'multiverse'
  END AS source
RETURN coalesce(su.id, sm.id) AS system_id, source
