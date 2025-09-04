MATCH (st:Story)-[:HAS_SCENE]->(sc:Scene {id:$sid})
CALL {
  WITH sc, st
  MATCH (rs:RelationState)-[:REL_STATE_FOR {endpoint:'A'}]->(:Entity {id:$a})
  MATCH (rs)-[:REL_STATE_FOR {endpoint:'B'}]->(:Entity {id:$b})
  OPTIONAL MATCH (rs)-[:SET_IN_SCENE]->(s_set:Scene)
  OPTIONAL MATCH (rs)-[:CHANGED_IN_SCENE]->(s_chg:Scene)
  OPTIONAL MATCH (rs)-[:ENDED_IN_SCENE]->(s_end:Scene)
  OPTIONAL MATCH (st_set:Story)-[:HAS_SCENE]->(s_set)
  OPTIONAL MATCH (st_end:Story)-[:HAS_SCENE]->(s_end)
  WITH sc, st,
       (s_set IS NOT NULL AND s_set.id = sc.id) AS set_here,
       (s_chg IS NOT NULL AND s_chg.id = sc.id) AS changed_here,
       (s_end IS NOT NULL AND s_end.id = sc.id) AS ended_here,
       (st_set = st AND s_set.sequence_index IS NOT NULL AND sc.sequence_index IS NOT NULL AND s_set.sequence_index <= sc.sequence_index) AS set_before_cur_story,
       (st_end = st AND s_end.sequence_index IS NOT NULL AND sc.sequence_index IS NOT NULL AND s_end.sequence_index <= sc.sequence_index) AS ended_by_cur_story
  RETURN ((set_here OR changed_here OR set_before_cur_story) AND NOT (ended_here OR ended_by_cur_story)) AS active
}
RETURN active AS active
