MATCH (st:Story)-[:HAS_SCENE]->(sc:Scene {id:$sid})
MATCH (a:Axiom)-[:APPLIES_TO]->(st)
RETURN a.id AS id, a.name AS name, a.description AS description
ORDER BY a.name