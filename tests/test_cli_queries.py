import sys
from pathlib import Path
from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]
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
        def relation_state_history(self, *_):
            return []
        def axioms_applying_to_universe(self, _):
            return []

    import core.interfaces.cli_interface as cli
    monkeypatch.setattr(cli, "Neo4jRepo", lambda: FakeRepo())
    monkeypatch.setattr(cli, "QueryService", FakeService)

    for sub in [
        ["q", "entities-in-scene", "SC-1"],
        ["q", "facts-for-scene", "SC-2"],
        ["q", "relation-history", "E-1", "E-2"],
        ["q", "axioms-for-universe", "U-1"],
    ]:
        res = runner.invoke(app, sub)
        assert res.exit_code == 0
        assert res.output.strip().startswith("[") or res.output.strip().startswith("[")
