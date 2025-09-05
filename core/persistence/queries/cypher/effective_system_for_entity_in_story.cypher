MATCH (e:Entity {id:$eid})
MATCH (st:Story {id:$sid})
OPTIONAL MATCH (e)-[:APPEARS_IN]->(sc:Scene)<-[:HAS_SCENE]-(st)
OPTIONAL MATCH (st)-[:USES_SYSTEM]->(sys:System)
RETURN sys.id AS id, sys.name AS name, sys.description AS description