MATCH (:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
RETURN sc.id AS id, sc.title AS title, sc.sequence_index AS sequence_index
ORDER BY sequence_index
