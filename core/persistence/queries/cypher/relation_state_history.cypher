MATCH (rs:RelationState)-[:REL_STATE_FOR {endpoint:'A'}]->(a:Entity {id:$a})
MATCH (rs)-[:REL_STATE_FOR {endpoint:'B'}]->(b:Entity {id:$b})
RETURN rs.id AS id, rs.state AS state, rs.created_at AS created_at
ORDER BY rs.created_at DESC