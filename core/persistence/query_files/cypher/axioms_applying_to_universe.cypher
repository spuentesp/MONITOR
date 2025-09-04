MATCH (a:Axiom)-[:APPLIES_TO]->(u:Universe {id:$uid})
OPTIONAL MATCH (a)-[:REFERS_TO]->(ar:Archetype)
RETURN a.id AS id, a.type AS type, a.semantics AS semantics, ar.id AS refers_to_archetype
ORDER BY id
