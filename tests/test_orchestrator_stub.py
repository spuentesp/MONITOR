from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.engine.orchestrator import Orchestrator, OrchestratorConfig  # noqa: E402
from core.engine.tools import ToolContext  # noqa: E402
from core.generation.mock_llm import MockLLM  # noqa: E402


class DummyQueryService:
    def relations_effective_in_scene(self, scene_id: str):
        return [{"a": "e:1", "b": "e:2", "type": "ALLY"}]


def test_orchestrator_stub_runs():
    ctx = ToolContext(query_service=DummyQueryService())
    orch = Orchestrator(MockLLM(), tools=ctx, config=OrchestratorConfig(mode="copilot"))
    out = orch.step("Introduce a rival in the alley.", scene_id="scene:1")
    assert out["plan"]["beats"]
    assert isinstance(out["draft"], str) and len(out["draft"]) > 0
    assert out["commit"]["mode"] == "dry_run"
