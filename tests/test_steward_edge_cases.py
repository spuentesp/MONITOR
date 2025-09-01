from __future__ import annotations

from core.engine.steward import StewardService


class QFake:
    def entities_in_scene(self, scene_id: str):
        return [{"id": "e_in"}]


def test_steward_warnings_and_errors():
    svc = StewardService(QFake())
    deltas = {
        "scene_id": "s1",
        "facts": [
            {"participants": [{"entity_id": "e_missing"}]},
            {"time_span": {"start": "2025-12-31", "end": "2025-01-01"}},
        ],
        "relation_states": [
            {"entity_a": None, "entity_b": "e2"},
            {"entity_a": "x", "entity_b": "x"},
        ],
    }
    ok, warns, errs = svc.validate(deltas)
    assert ok is False
    # Should include at least one warning and one error
    assert any("Participant" in w for w in warns)
    assert any("start > end" in e or "missing entity_a" in e for e in errs)
