MATCH (st:Story)-[:HAS_SCENE]->(sc:Scene {id:$sid})
MATCH (rs:RelationState)-[:OCCURS_IN]->(sc)
RETURN rs.id AS id, rs.state AS state
ORDER BY rs.created_at DESC