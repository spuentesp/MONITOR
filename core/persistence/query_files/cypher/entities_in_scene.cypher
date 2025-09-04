MATCH (e:Entity)-[:APPEARS_IN]->(s:Scene {id:$sid})
RETURN e.id AS id, e.name AS name, e.type AS type
ORDER BY name
