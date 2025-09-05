MATCH (st:Story)-[:HAS_SCENE]->(sc:Scene {id:$sid})
MATCH (rs:RelationState)-[:REL_STATE_FOR {endpoint:'A'}]->(a:Entity {id:$a})
MATCH (rs)-[:REL_STATE_FOR {endpoint:'B'}]->(b:Entity {id:$b})
MATCH (rs)-[:OCCURS_IN]->(sc)
RETURN rs.state = 'active' AS active