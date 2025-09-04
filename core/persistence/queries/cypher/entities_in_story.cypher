MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
MATCH (e:Entity)-[:APPEARS_IN]->(sc)
RETURN DISTINCT e.id AS id, e.name AS name
ORDER BY name
