from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from core.interfaces.api_interface import app
from tests.conftest import make_ctx_header

pytestmark = pytest.mark.integration

client = TestClient(app)


def _ctx_header():
    return make_ctx_header()


def test_resolve_endpoint_error_branch_stages_anyway():
    payload = {
        "deltas": {"relation_states": [{"entity_a": None, "entity_b": None}], "scene_id": None},
        "mode": "copilot",
        "commit": False,
    }
    r = client.post("/resolve", json=payload, headers=_ctx_header())
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False and "commit" in body and body["commit"]["mode"] == "dry_run"
