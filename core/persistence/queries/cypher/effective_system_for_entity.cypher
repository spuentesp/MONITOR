MATCH (e:Entity {id:$eid})
OPTIONAL MATCH (e)-[:USES_SYSTEM]->(sys:System)
RETURN sys.id AS id, sys.name AS name, sys.description AS description