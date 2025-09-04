-- System usage summary across a universe
-- Parameters: $uid (universe_id)
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
