from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

import json

from typer.testing import CliRunner

from core.interfaces.cli_interface import app

runner = CliRunner()


def test_cli_help_runs():
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0


def test_cli_queries_help_runs():
    r = runner.invoke(app, ["q", "--help"])
    assert r.exit_code == 0


def test_cli_resolve_deltas_dry_run(monkeypatch):
    # Monkeypatch orchestrator.Neo4jRepo used by build_live_tools to a no-op stub
    import core.engine.orchestrator as orch

    class FakeRepo:
        def connect(self):
            return self

        def close(self):
            pass

        def ping(self):
            return False

        def run(self, *_a, **_k):
            return []

    orch.Neo4jRepo = FakeRepo  # type: ignore

    with runner.isolated_filesystem():
        path = "deltas.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"facts": [{"description": "x"}]}, f)
        r = runner.invoke(app, ["resolve-deltas", path])
        assert r.exit_code == 0
