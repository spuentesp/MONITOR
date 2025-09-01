import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.persistence.neo4j_repo import Neo4jRepo  # noqa: E402
from core.persistence.recorder import RecorderService  # noqa: E402


def neo4j_available():
    try:
        Neo4jRepo().connect().close()
        return True
    except Exception:
        return False


requires_neo4j = pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")


@requires_neo4j
def test_recorder_live_creates_entity_scene_fact_and_relstate():
    repo = Neo4jRepo().connect()
    try:
        repo.bootstrap_constraints()
        repo.bootstrap_indexes()
        recorder = RecorderService(repo)

        # Ensure a minimal universe, story, and heroes exist
        repo.run("MERGE (u:Universe {id:'U-616'}) RETURN u")
        repo.run("MERGE (s:Story {id:'story-nyc-patrol'}) RETURN s")
        repo.run("MATCH (u:Universe {id:'U-616'}), (s:Story {id:'story-nyc-patrol'}) MERGE (u)-[:HAS_STORY]->(s)")
        repo.run("MERGE (e:Entity {id:'ent-rogue'}) RETURN e")
        repo.run("MERGE (e:Entity {id:'ent-spidey'}) RETURN e")

        out = recorder.commit_deltas(
            scene_id=None,
            universe_id="U-616",
            new_entities=[{"id": "ent-jimmy", "name": "Jimmy"}],
            new_scene={
                "id": "sc-jimmy-intro",
                "story_id": "story-nyc-patrol",
                "sequence_index": 3,
                "participants": ["ent-rogue", "ent-spidey", "ent-jimmy"],
            },
            facts=[
                {
                    "id": "fact-convince-jimmy",
                    "description": "Rogue and Spider-Man convince Jimmy to help",
                    "participants": [
                        {"entity_id": "ent-rogue", "role": "convincer"},
                        {"entity_id": "ent-spidey", "role": "convincer"},
                        {"entity_id": "ent-jimmy", "role": "ally"},
                    ],
                }
            ],
            relation_states=[
                {"type": "friend_of", "entity_a": "ent-jimmy", "entity_b": "ent-rogue"},
                {"type": "friend_of", "entity_a": "ent-jimmy", "entity_b": "ent-spidey"},
            ],
        )

        assert out["ok"]
        # Verify graph has expected nodes/edges
        rows = repo.run(
            """
            MATCH (sc:Scene {id:'sc-jimmy-intro'})
            MATCH (j:Entity {id:'ent-jimmy'})-[:APPEARS_IN]->(sc)
            MATCH (:Entity {id:'ent-rogue'})-[:APPEARS_IN]->(sc)
            MATCH (:Entity {id:'ent-spidey'})-[:APPEARS_IN]->(sc)
            MATCH (f:Fact {id:'fact-convince-jimmy'})-[:OCCURS_IN]->(sc)
            MATCH (:Entity {id:'ent-jimmy'})<-[:REL_STATE_FOR]-(:RelationState {type:'friend_of'})-[:REL_STATE_FOR]->(:Entity {id:'ent-rogue'})
            MATCH (:Entity {id:'ent-jimmy'})<-[:REL_STATE_FOR]-(:RelationState {type:'friend_of'})-[:REL_STATE_FOR]->(:Entity {id:'ent-spidey'})
            RETURN count(*) AS ok
            """
        )
        assert rows and rows[0]["ok"] >= 1
    finally:
        repo.close()
