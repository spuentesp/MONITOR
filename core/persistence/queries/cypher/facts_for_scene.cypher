MATCH (f:Fact)-[:OCCURS_IN]->(s:Scene {id:$sid})
OPTIONAL MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
WITH f, collect({entity_id:e.id, role:p.role}) AS participants
RETURN f.id AS id, f.description AS description, participants
ORDER BY id
