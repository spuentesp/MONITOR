MATCH (st:Story)-[:HAS_SCENE]->(sc:Scene {id:$sid})
CALL {
  WITH sc, st
  MATCH (rs:RelationState)
  MATCH (rs)-[:REL_STATE_FOR {endpoint:'A'}]->(a:Entity)
  MATCH (rs)-[:REL_STATE_FOR {endpoint:'B'}]->(b:Entity)
  OPTIONAL MATCH (rs)-[:SET_IN_SCENE]->(s_set:Scene)
  OPTIONAL MATCH (rs)-[:CHANGED_IN_SCENE]->(s_chg:Scene)
  OPTIONAL MATCH (rs)-[:ENDED_IN_SCENE]->(s_end:Scene)
  OPTIONAL MATCH (st_set:Story)-[:HAS_SCENE]->(s_set)
  OPTIONAL MATCH (st_end:Story)-[:HAS_SCENE]->(s_end)
  WITH rs, a, b, sc, st,
       s_set, s_chg, s_end, st_set, st_end,
       (s_set IS NOT NULL AND s_set.id = sc.id) AS set_here,
       (s_chg IS NOT NULL AND s_chg.id = sc.id) AS changed_here,
       (s_end IS NOT NULL AND s_end.id = sc.id) AS ended_here,
       (st_set = st AND s_set.sequence_index IS NOT NULL AND sc.sequence_index IS NOT NULL AND s_set.sequence_index <= sc.sequence_index) AS set_before_cur_story,
       (st_end = st AND s_end.sequence_index IS NOT NULL AND sc.sequence_index IS NOT NULL AND s_end.sequence_index <= sc.sequence_index) AS ended_by_cur_story
  WITH rs, a, b, sc,
       ((set_here OR changed_here OR set_before_cur_story) AND NOT (ended_here OR ended_by_cur_story)) AS active
  WHERE active
  RETURN rs, a, b
}
RETURN rs.id AS id, rs.type AS type, a.id AS entity_a, b.id AS entity_b
ORDER BY id
