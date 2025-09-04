MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
MATCH (f:Fact)-[:OCCURS_IN]->(sc)
MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
WHERE p.role = $role
RETURN DISTINCT e.id AS id, e.name AS name
ORDER BY name
