MATCH (e:Entity {id:$eid})-[:APPEARS_IN]->(sc:Scene)
OPTIONAL MATCH (st:Story)-[:HAS_SCENE]->(sc)
RETURN sc.id AS scene_id, st.id AS story_id, sc.sequence_index AS sequence_index
ORDER BY story_id, sequence_index
