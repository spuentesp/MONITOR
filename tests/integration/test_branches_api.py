from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from core.interfaces.api_interface import app
from tests.conftest import make_ctx_header

pytestmark = pytest.mark.integration


client = TestClient(app)


def _ctx_header():
    return make_ctx_header()


def test_branches_router_present():
    r = client.get("/openapi.json")
    assert r.status_code == 200
    data = r.json()
    paths = data.get("paths", {})
    assert any(p.startswith("/api/branches/") for p in paths.keys())


def test_branch_at_scene_calls_service(monkeypatch):
    calls: list[tuple[str, dict]] = []

    class FakeRepo:
        def connect(self):
            return self

    class FakeSvc:
        def __init__(self, _repo):
            pass

        def branch_universe_at_scene(self, **kw):  # type: ignore[no-untyped-def]
            calls.append(("branch_universe_at_scene", kw))
            return {"new_universe_id": kw["new_universe_id"], "counts": {"facts": 3}}

    # Patch repo and service factory used by endpoints
    import core.interfaces.branches_api as mod

    monkeypatch.setattr(mod, "Neo4jRepo", lambda: FakeRepo())
    monkeypatch.setattr(mod, "BranchService", lambda repo: FakeSvc(repo))

    payload = {
        "source_universe_id": "U-1",
        "divergence_scene_id": "ST-1/SC-3",
        "new_universe_id": "U-1b",
        "new_universe_name": "Branched",
        "dry_run": True,
    }
    r = client.post("/api/branches/branch-at-scene", json=payload, headers=_ctx_header())
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True and body["result"]["new_universe_id"] == "U-1b"
    assert calls and calls[0][0] == "branch_universe_at_scene"


def test_clone_full_and_subset(monkeypatch):
    class FakeRepo:
        def connect(self):
            return self

    class FakeSvc:
        def __init__(self, _repo):
            pass

        def clone_universe_full(self, **kw):  # type: ignore[no-untyped-def]
            return {"new_universe_id": kw["new_universe_id"], "mode": "full"}

        def clone_universe_subset(self, **kw):  # type: ignore[no-untyped-def]
            return {"new_universe_id": kw["new_universe_id"], "mode": "subset"}

    import core.interfaces.branches_api as mod

    monkeypatch.setattr(mod, "Neo4jRepo", lambda: FakeRepo())
    monkeypatch.setattr(mod, "BranchService", lambda repo: FakeSvc(repo))

    base = {
        "source_universe_id": "U-1",
        "new_universe_id": "U-1c",
        "new_universe_name": "Clone",
        "dry_run": True,
    }
    r1 = client.post("/api/branches/clone", json={**base, "mode": "full"}, headers=_ctx_header())
    r2 = client.post(
        "/api/branches/clone",
        json={**base, "mode": "subset", "stories": ["ST-1"], "scene_max_index": 2},
        headers=_ctx_header(),
    )
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["result"]["mode"] == "full"
    assert r2.json()["result"]["mode"] == "subset"


def test_diff_shape(monkeypatch):
    # We don't need full DB; just ensure endpoint constructs and returns expected schema
    class FakeRepo:
        def connect(self):
            return self

        def run(self, q, **params):  # type: ignore[no-untyped-def]
            return [{"c": 0}]

    import core.interfaces.branches_api as mod

    monkeypatch.setattr(mod, "Neo4jRepo", lambda: FakeRepo())

    r = client.get("/api/branches/U-1/diff/U-2", headers=_ctx_header())
    assert r.status_code == 200
    data = r.json()
    assert data["source_universe_id"] == "U-1"
    assert data["target_universe_id"] == "U-2"
    assert set(data["counts"].keys()) == {
        "stories_only_in_source",
        "stories_only_in_target",
        "entities_only_in_source",
        "entities_only_in_target",
        "facts_only_in_source",
        "facts_only_in_target",
    }


def test_typed_diff_and_append_missing(monkeypatch):
    class FakeRepo:
        def connect(self):
            return self

        def run(self, q, **params):  # type: ignore[no-untyped-def]
            # Return simple empty/zero responses, except count aggregations
            qn = " ".join(q.split())
            if "RETURN collect" in qn:
                return [{"ids": []}]
            if "RETURN count(" in qn:
                return [{"c": 0}]
            if "RETURN count(DISTINCT" in qn and "AS inserted" in qn:
                return [{"inserted": 0}]
            return [{"c": 0}]

    import core.interfaces.branches_api as mod

    monkeypatch.setattr(mod, "Neo4jRepo", lambda: FakeRepo())

    r = client.get("/api/branches/U-1/diff/U-2/typed", headers=_ctx_header())
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) >= {"stories", "scenes", "entities", "facts", "provenance"}

    # Append missing should succeed with ops counter
    r2 = client.post(
        "/api/branches/promote",
        json={
            "source_universe_id": "U-1",
            "target_universe_id": "U-2",
            "strategy": "append_missing",
        },
        headers=_ctx_header(),
    )
    assert r2.status_code == 200
    assert "ops" in r2.json()
