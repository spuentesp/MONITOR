MATCH (m:Multiverse {id:$mid})-[:HAS_UNIVERSE]->(u:Universe)
RETURN u.id AS id, u.name AS name
ORDER BY name, id
