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
