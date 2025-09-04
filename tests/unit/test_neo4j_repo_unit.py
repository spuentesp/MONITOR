import pytest

pytestmark = pytest.mark.unit

import types

import core.persistence.neo4j_repo as mod


class DummySession:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def run(self, cypher, **params):  # pragma: no cover - trivial
        return []


class DummyDriver:
    def __init__(self, *args, **kwargs):
        pass

    def session(self):
        return DummySession()

    def close(self):
        pass


def test_repo_connect_and_run_monkeypatched(monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "bolt://x")
    monkeypatch.setenv("NEO4J_USER", "u")
    monkeypatch.setenv("NEO4J_PASS", "p")
    monkeypatch.setattr(
        mod, "GraphDatabase", types.SimpleNamespace(driver=lambda *a, **k: DummyDriver())
    )

    repo = mod.Neo4jRepo().connect()
    assert repo.ping() is True
    repo.bootstrap_constraints()  # should not raise
    repo.close()
