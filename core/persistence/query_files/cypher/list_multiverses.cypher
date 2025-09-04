MATCH (m:Multiverse)
RETURN m.id AS id, m.name AS name
ORDER BY name, id
