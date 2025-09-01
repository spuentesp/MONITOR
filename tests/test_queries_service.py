import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.persistence.queries import QueryService  # noqa: E402


class FakeRepo:
    def __init__(self):
        self.last = None

    def run(self, cypher: str, **params):
        self.last = (" ".join(cypher.split()), params)
        return []


def test_queries_shapes():
    repo = FakeRepo()
    svc = QueryService(repo)

    svc.entities_in_scene("SC-1")
    assert "MATCH (e:Entity)-[:APPEARS_IN]->(s:Scene {id:$sid})" in repo.last[0]

    svc.entities_in_story("ST-1")
    assert "MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)" in repo.last[0]

    svc.facts_for_scene("SC-9")
    assert "MATCH (f:Fact)-[:OCCURS_IN]->(s:Scene {id:$sid})" in repo.last[0]

    svc.relation_state_history("E-1", "E-2")
    text, params = repo.last
    assert "MATCH (rs:RelationState)-[:REL_STATE_FOR {endpoint:'A'}]->(a:Entity {id:$a})" in text
    assert params["a"] == "E-1" and params["b"] == "E-2"

    svc.axioms_applying_to_universe("U-1")
    assert "MATCH (a:Axiom)-[:APPLIES_TO]->(u:Universe {id:$uid})" in repo.last[0]

    svc.scenes_for_entity("E-5")
    assert "MATCH (e:Entity {id:$eid})-[:APPEARS_IN]->(sc:Scene)" in repo.last[0]

    svc.entities_in_arc("ARC-1")
    assert "MATCH (a:Arc {id:$aid})-[:HAS_STORY]->(st:Story)" in repo.last[0]

    svc.facts_for_story("ST-2")
    assert "MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)" in repo.last[0]

    svc.system_usage_summary("U-1")
    assert "MATCH (u:Universe {id:$uid})" in repo.last[0]

    svc.axioms_effective_in_scene("SC-7")
    assert "MATCH (st:Story)-[:HAS_SCENE]->(sc:Scene {id:$sid})" in repo.last[0]

    svc.entities_in_universe("U-1")
    assert "MATCH (u:Universe {id:$uid})-[:HAS_STORY]->(st:Story)" in repo.last[0]

    svc.entities_in_story_by_role("ST-1", "rescuer")
    assert "WHERE p.role = $role" in repo.last[0]

    svc.entities_in_arc_by_role("ARC-9", "antagonist")
    assert "MATCH (a:Arc {id:$aid})-[:HAS_STORY]->(st:Story)" in repo.last[0]

    svc.entities_in_universe_by_role("U-2", "guardian")
    assert "MATCH (u:Universe {id:$uid})-[:HAS_STORY]->(st:Story)" in repo.last[0]

    svc.participants_by_role_for_scene("SC-1")
    assert "WITH p.role AS role" in repo.last[0]

    svc.participants_by_role_for_story("ST-2")
    assert "WITH p.role AS role" in repo.last[0]

    svc.next_scene_for_entity_in_story("ST-1", "E-1", 1)
    assert "ORDER BY sequence_index ASC" in repo.last[0]

    svc.previous_scene_for_entity_in_story("ST-1", "E-1", 3)
    assert "ORDER BY sequence_index DESC" in repo.last[0]
