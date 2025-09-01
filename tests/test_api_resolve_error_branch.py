from __future__ import annotations

from fastapi.testclient import TestClient

from core.interfaces.api_interface import app

client = TestClient(app)


def _ctx_header():
    from core.engine.context import ContextToken

    t = ContextToken(omniverse_id="o1", multiverse_id="m1", universe_id="u1").model_dump_json()
    return {"X-Context-Token": t}


def test_resolve_endpoint_error_branch_stages_anyway():
    # Missing entity ids in relation_states should produce errors (ok=False)
    payload = {"deltas": {"relation_states": [{"entity_a": None, "entity_b": None}], "scene_id": None}, "mode": "copilot", "commit": False}
    r = client.post("/resolve", json=payload, headers=_ctx_header())
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False and "commit" in body and body["commit"]["mode"] == "dry_run"
