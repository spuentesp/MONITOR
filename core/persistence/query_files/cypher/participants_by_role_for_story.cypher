MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
MATCH (f:Fact)-[:OCCURS_IN]->(sc)
MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
WITH p.role AS role, collect(DISTINCT e.id) AS entities
RETURN role, entities
ORDER BY role
