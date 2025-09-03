from __future__ import annotations

from fastapi.testclient import TestClient

from core.interfaces.api_interface import app

client = TestClient(app)


def _ctx_header():
    # Minimal valid token
    from core.engine.context import ContextToken

    t = ContextToken(omniverse_id="o1", multiverse_id="m1", universe_id="u1").model_dump_json()
    return {"X-Context-Token": t}


def test_health_and_root_public():
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200


def test_config_agents_requires_token():
    r = client.get("/config/agents")
    assert r.status_code == 400
    r = client.get("/config/agents", headers=_ctx_header())
    assert r.status_code == 200


def test_validate_endpoint():
    r = client.post("/validate", json={"deltas": {}}, headers=_ctx_header())
    assert r.status_code == 200
    data = r.json()
    assert "ok" in data and "warnings" in data and "errors" in data


def test_step_and_chat_endpoints():
    r = client.post("/step", json={"intent": "hello", "mode": "copilot"}, headers=_ctx_header())
    assert r.status_code == 200
    data = r.json()
    assert "draft" in data and "summary" in data

    payload = {
        "turns": [{"content": "hi", "scene_id": None}],
        "mode": "copilot",
        "persist_each": False,
    }
    r2 = client.post("/chat", json=payload, headers=_ctx_header())
    assert r2.status_code == 200
    assert "steps" in r2.json()


def test_chat_persist_each_and_step_record_fact_and_flush():
    # persist_each uses recorder_tool in dry-run; just exercise path
    payload = {
        "turns": [{"content": "there", "scene_id": "s1"}],
        "mode": "copilot",
        "persist_each": True,
    }
    r = client.post("/chat", json=payload, headers=_ctx_header())
    assert r.status_code == 200

    # step with record_fact should attach persisted key (dry-run)
    r2 = client.post(
        "/step", json={"intent": "x", "scene_id": "s1", "record_fact": True}, headers=_ctx_header()
    )
    assert r2.status_code == 200
    assert "persisted" in r2.json()

    # staging flush endpoint
    r3 = client.post("/staging/flush", headers=_ctx_header())
    assert r3.status_code == 200


def test_resolve_endpoint_stages_by_default():
    payload = {
        "deltas": {"facts": [{"description": "x"}], "scene_id": None},
        "mode": "copilot",
        "commit": False,
    }
    r = client.post("/resolve", json=payload, headers=_ctx_header())
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] in [True, False] and "commit" in body
