MATCH (st:Story)-[:HAS_SCENE]->(sc:Scene {id:$sid})
MATCH (u:Universe)-[:HAS_STORY]->(st)
MATCH (a:Axiom)-[:APPLIES_TO]->(u)
OPTIONAL MATCH (a)-[:REFERS_TO]->(ar:Archetype)
RETURN a.id AS id, a.type AS type, a.semantics AS semantics, ar.id AS refers_to_archetype
ORDER BY id
