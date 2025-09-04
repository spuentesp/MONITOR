MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
MATCH (f:Fact)-[:OCCURS_IN]->(sc)
OPTIONAL MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
WITH f, collect({entity_id:e.id, role:p.role}) AS participants
RETURN f.id AS id, f.description AS description, participants
ORDER BY id
