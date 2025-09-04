MATCH (u:Universe {id:$uid})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(:Scene)<-[:APPEARS_IN]-(e:Entity)
WHERE toLower(e.name) = toLower($name)
RETURN e.id AS id, e.name AS name, e.type AS type
LIMIT 1
