MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
WHERE sc.sequence_index < $idx
MATCH (e:Entity {id:$eid})-[:APPEARS_IN]->(sc)
RETURN sc.id AS scene_id, sc.sequence_index AS sequence_index
ORDER BY sequence_index DESC
LIMIT 1
