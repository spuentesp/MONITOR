MATCH (u:Universe {id:$uid})-[:HAS_STORY]->(st:Story)
OPTIONAL MATCH (a:Arc)-[:HAS_STORY]->(st)
RETURN st.id AS id, st.title AS title, st.sequence_index AS sequence_index,
       a.id AS arc_id
ORDER BY sequence_index, title
