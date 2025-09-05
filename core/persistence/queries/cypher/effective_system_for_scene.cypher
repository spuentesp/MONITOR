MATCH (st:Story)-[:HAS_SCENE]->(sc:Scene {id:$sid})
OPTIONAL MATCH (st)-[:USES_SYSTEM]->(sys:System)
RETURN sys.id AS id, sys.name AS name, sys.description AS description