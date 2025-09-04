MATCH (a:Arc {id:$aid})-[:HAS_STORY]->(st:Story)
MATCH (st)-[:HAS_SCENE]->(sc:Scene)
MATCH (e:Entity)-[:APPEARS_IN]->(sc)
RETURN DISTINCT e.id AS id, e.name AS name
ORDER BY name
