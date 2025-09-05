MATCH (a:Axiom)-[:APPLIES_TO]->(u:Universe {id:$uid})
RETURN a.id AS id, a.name AS name, a.description AS description
ORDER BY a.name