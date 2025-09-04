from pathlib import Path
import sys

import pytest

pytestmark = pytest.mark.integration

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.interfaces.cli_interface import app  # noqa: E402


def test_cli_query_commands_exist_and_print_json(monkeypatch):
    runner = CliRunner()

    class FakeRepo:
        def connect(self):
            return self

        def close(self):
            pass

    class FakeService:
        def __init__(self, repo):
            pass

        def entities_in_scene(self, _):
            return []

        def facts_for_scene(self, _):
            return []

        def facts_for_story(self, _):
            return []

        def relation_state_history(self, *_):
            return []

        def axioms_applying_to_universe(self, _):
            return []

        def entities_in_arc(self, _):
            return []

        def system_usage_summary(self, _):
            return []

        def axioms_effective_in_scene(self, _):
            return []

        # Branching
        def branch_universe_at_scene(self, *_args):
            return {"ok": True}

        def clone_universe(self, *_args):
            return {"ok": True}

        def clone_universe_subset(self, *_args, **kwargs):
            return {"ok": True}

    import core.interfaces.cli_interface as cli

    monkeypatch.setattr(cli, "Neo4jRepo", lambda: FakeRepo())
    monkeypatch.setattr(cli, "QueryService", FakeService)
    monkeypatch.setattr(cli, "BranchService", FakeService)

    for sub in [
        ["q", "entities-in-scene", "SC-1"],
        ["q", "facts-for-scene", "SC-2"],
        ["q", "facts-for-story", "ST-2"],
        ["q", "relation-history", "E-1", "E-2"],
        ["q", "axioms-for-universe", "U-1"],
        ["q", "entities-in-arc", "ARC-1"],
        ["q", "system-usage", "U-1"],
        ["q", "axioms-in-scene", "SC-7"],
        ["branch-universe", "U-1", "SC-3", "U-1b"],
        ["clone-universe", "U-1", "U-1c"],
        [
            "clone-universe-subset",
            "U-1",
            "U-1s",
            "--stories",
            "ST-1,ST-2",
            "--arcs",
            "ARC-1",
            "--scene-max-index",
            "2",
        ],
    ]:
        res = runner.invoke(app, sub)
    assert res.exit_code == 0
    out = res.output.strip()
    assert out.startswith("[") or out.startswith("{")
