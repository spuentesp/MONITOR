from __future__ import annotations

from typing import Any

from core.persistence.recorder import RecorderService


class DummyRepo:
    def __init__(self):
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def ping(self) -> bool:
        return False

    def run(self, q: str, **params: Any):
        self.calls.append((q.strip().split("\n")[0], params))
        return []


def test_recorder_facts_relations_and_states_paths():
    repo = DummyRepo()
    svc = RecorderService(repo)
    res = svc.commit_deltas(
        scene_id="s1",
        universe_id="u1",
        facts=[{"description": "d", "participants": [{"entity_id": "e1", "role": "pc"}]}],
        relation_states=[
            {"type": "ally", "entity_a": "e1", "entity_b": "e2", "set_in_scene": "s1"}
        ],
        relations=[{"a": "e1", "b": "e2", "type": "ally", "weight": 1}],
    )
    assert res["ok"] and res["written"]["facts"] == 1 and res["written"]["relation_states"] == 1 and res["written"]["relations"] == 1


class FakeRepo:
    def __init__(self):
        self.calls = []

    def run(self, cypher: str, **params):
        self.calls.append((cypher.strip(), params))
        return []


def test_recorder_can_create_emergent_npc_scene_fact_and_relations():
    repo = FakeRepo()
    recorder = RecorderService(repo)  # duck-typed repo

    # Universe context exists (heroes already exist in DB, but we don't hit DB here)
    universe_id = "U-616"

    # New NPC Jimmy + a new Scene where Rogue and Spider-Man convince him
    res = recorder.commit_deltas(
        scene_id=None,
        universe_id=universe_id,
        new_entities=[
            {
                "id": "ent-jimmy",
                "name": "Jimmy",
                "type": "character",
                "attributes": {
                    "mutant": True,
                    "traits": {"skin": "lizard", "feeds_on": "sunlight"},
                },
            }
        ],
        new_scene={
            "id": "sc-jimmy-intro",
            "story_id": "story-nyc-patrol",
            "sequence_index": 3,
            "when": "2010-06-01",
            "location": "NYC Rooftops",
            "participants": ["ent-rogue", "ent-spidey", "ent-jimmy"],
        },
        facts=[
            {
                "id": "fact-convince-jimmy",
                "description": "Rogue and Spider-Man convince Jimmy to help",
                # occurs_in omitted -> defaults to the new scene
                "participants": [
                    {"entity_id": "ent-rogue", "role": "convincer"},
                    {"entity_id": "ent-spidey", "role": "convincer"},
                    {"entity_id": "ent-jimmy", "role": "ally"},
                ],
                "confidence": 0.9,
            }
        ],
        relation_states=[
            {
                "id": "relstate-jimmy-rogue-friend",
                "type": "friend_of",
                "entity_a": "ent-jimmy",
                "entity_b": "ent-rogue",
                # set_in_scene omitted -> defaults to the new scene
            },
            {
                "id": "relstate-jimmy-spidey-friend",
                "type": "friend_of",
                "entity_a": "ent-jimmy",
                "entity_b": "ent-spidey",
            },
        ],
    )

    assert res["ok"] is True
    w = res["written"]
    # 1 new entity (Jimmy), 1 new scene, 3 APPEARS_IN edges, 1 fact, 2 relation states
    assert w["entities"] == 1
    assert w["scenes"] == 1
    assert w["appears_in"] == 3
    assert w["facts"] == 1
    assert w["relation_states"] == 2
