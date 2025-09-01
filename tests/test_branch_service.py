import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.persistence.brancher import BranchService  # noqa: E402


class FakeRepo:
    def __init__(self):
        self.calls = []
        # Preload first query result: resolve story and idx
        self._next = [[{"story_id": "ST-1", "idx": 3}]]

    def run(self, cypher: str, **params):
        self.calls.append((" ".join(cypher.split()), params))
        if self._next:
            return self._next.pop(0)
        return []


def test_branch_service_emits_expected_cypher_sequence():
    repo = FakeRepo()
    svc = BranchService(repo)
    out = svc.branch_universe_at_scene("U-1", "SC-3", "U-1b", "Branched U")
    assert out["new_universe_id"] == "U-1b"
    # First call resolves divergence info
    q1, p1 = repo.calls[0]
    assert "MATCH (u:Universe {id:$src_uid})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene {id:$sid})" in q1
    # Second ensures new universe and provenance
    q2, p2 = repo.calls[1]
    assert "MERGE (u2:Universe {id:$new_uid})" in q2 and "BRANCHED_FROM" in q2
    # Story cloning
    q3, _ = repo.calls[2]
    assert "MERGE (st2:Story {id:$new_sid})" in q3 and "HAS_STORY" in q3
    # Scenes cloning includes sequence filter and BRANCHED_FROM
    q4, _ = repo.calls[3]
    assert "WHERE sc.sequence_index <= $idx" in q4 and "MERGE (sc2)-[:BRANCHED_FROM]->(sc)" in q4
    # Entities cloning and APPEARS_IN on cloned scenes
    q5, _ = repo.calls[4]
    q6, _ = repo.calls[5]
    assert "MERGE (e2:Entity {id: $new_uid + '/' + e.id})" in q5
    assert "MERGE (e2)-[:APPEARS_IN]->(sc2)" in q6
    # Facts cloning and participants
    q7, _ = repo.calls[6]
    q8, _ = repo.calls[7]
    assert "MERGE (f2:Fact {id: $new_uid + '/' + f.id})" in q7
    assert "MERGE (e2)-[:PARTICIPATES_AS {role: p.role}]->(f2)" in q8
    # Sheets cloning
    q9, _ = repo.calls[8]
    assert "MERGE (sh2:Sheet {id: $new_uid + '/' + sh.id})" in q9
    # RelationState cloning
    q10, _ = repo.calls[9]
    assert "MERGE (rs2:RelationState {id: $new_uid + '/' + rs.id})" in q10


def test_clone_universe_full_shapes():
    class R(FakeRepo):
        def __init__(self):
            super().__init__()
            self._next = []

    repo = R()
    svc = BranchService(repo)
    out = svc.clone_universe_full("U-1", "U-1c", "Clone U")
    assert out["new_universe_id"] == "U-1c"
    joined = "\n".join(q for q, _ in repo.calls)
    assert "MERGE (u2:Universe {id:$new_uid})" in joined
    assert "MERGE (st2:Story {id: $new_uid + '/' + st.id})" in joined
    assert "MERGE (sc2:Scene {id: $new_uid + '/' + st.id + '/' + sc.id})" in joined
    assert "MERGE (e2:Entity {id: $new_uid + '/' + e.id})" in joined
    assert "MERGE (f2:Fact {id: $new_uid + '/' + f.id})" in joined
    assert "MERGE (sh2:Sheet {id: $new_uid + '/' + sh.id})" in joined
    assert "MERGE (rs2:RelationState {id: $new_uid + '/' + rs.id})" in joined
    assert "MERGE (a2:Arc {id: $new_uid + '/' + a.id})" in joined
