MATCH (f:Fact)-[:OCCURS_IN]->(s:Scene {id:$sid})
MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
WITH p.role AS role, collect(DISTINCT e.id) AS entities
RETURN role, entities
ORDER BY role
