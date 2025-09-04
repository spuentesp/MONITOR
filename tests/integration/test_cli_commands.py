from __future__ import annotations
import pytest
pytestmark = pytest.mark.integration

from pathlib import Path

from typer.testing import CliRunner

from core.engine.tools import ToolContext
import core.interfaces.cli_interface as cli

runner = CliRunner()


class FakeRepo:
    def connect(self):
        return self

    def close(self):
        pass

    def ping(self):
        return True

    def bootstrap_constraints(self):
        return None


def test_cli_neo4j_bootstrap(monkeypatch):
    monkeypatch.setattr(cli, "Neo4jRepo", lambda: FakeRepo())
    r = runner.invoke(cli.app, ["neo4j-bootstrap"])  # should print OK and not crash
    assert r.exit_code == 0


def test_cli_project_from_yaml(monkeypatch, tmp_path: Path):
    class FakeProjector:
        def __init__(self, _repo):
            pass

        def project_from_yaml(self, path: Path, ensure_constraints: bool = True):
            assert Path(path).exists()

    monkeypatch.setattr(cli, "Neo4jRepo", lambda: FakeRepo())
    monkeypatch.setattr(cli, "Projector", FakeProjector)
    y = tmp_path / "mv.yaml"
    y.write_text("{}", encoding="utf-8")
    r = runner.invoke(cli.app, ["project-from-yaml", str(y)])
    assert r.exit_code == 0


def test_cli_orchestrate_step_with_record_fact(monkeypatch):
    # Avoid live tools by stubbing build_live_tools
    class Rec:
        def commit_deltas(self, **_kw):
            return {"ok": True, "written": {}}

    def fake_build_live_tools(dry_run: bool = True):
        return ToolContext(query_service=object(), recorder=Rec(), dry_run=dry_run)

    monkeypatch.setattr(cli, "build_live_tools", fake_build_live_tools)
    monkeypatch.setattr(cli, "run_once", lambda *a, **k: {"draft": "x"})
    r = runner.invoke(cli.app, ["orchestrate-step", "hi", "--scene-id", "s1", "--record-fact"])
    assert r.exit_code == 0


def test_cli_flush_staging(monkeypatch):
    class Staging:
        def flush(self, *_a, **_k):
            return {"ok": True}

    class Rec:
        def commit_deltas(self, **_kw):
            return {"ok": True}

    def fake_build_live_tools(dry_run: bool = False):
        return ToolContext(
            query_service=object(), recorder=Rec(), dry_run=dry_run, staging=Staging()
        )

    monkeypatch.setattr(cli, "build_live_tools", fake_build_live_tools)
    r = runner.invoke(cli.app, ["flush-staging"])
    assert r.exit_code == 0


def test_cli_weave_story(monkeypatch):
    def fake_build_live_tools(dry_run: bool = True):
        return ToolContext(query_service=object(), recorder=None, dry_run=dry_run)

    monkeypatch.setattr(cli, "build_live_tools", fake_build_live_tools)
    r = runner.invoke(cli.app, ["weave-story", "--beat", "a", "--beat", "b"])
    assert r.exit_code == 0


def test_cli_queries_subset(monkeypatch):
    class Q:
        def entities_in_scene(self, sid: str):
            return []

        def facts_for_scene(self, sid: str):
            return []

        def relation_state_history(self, a: str, b: str):
            return []

        def system_usage_summary(self, u: str):
            return {}

        def axioms_effective_in_scene(self, sid: str):
            return []

        def entities_in_universe(self, u: str):
            return []

    monkeypatch.setattr(cli, "Neo4jRepo", lambda: FakeRepo())
    monkeypatch.setattr(cli, "QueryService", lambda _repo: Q())
    cmds = [
        ("q", "entities-in-scene", "s1"),
        ("q", "facts-for-scene", "s1"),
        ("q", "relation-history", "e1", "e2"),
        ("q", "system-usage", "u1"),
        ("q", "axioms-in-scene", "s1"),
        ("q", "entities-in-universe", "u1"),
    ]
    for args in cmds:
        r = runner.invoke(cli.app, list(args))
        assert r.exit_code == 0
