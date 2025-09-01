import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import langgraph  # type: ignore
    HAS_LANGGRAPH = True
except Exception:
    HAS_LANGGRAPH = False

from core.generation.mock_llm import MockLLM  # noqa: E402
from core.agents.narrator import narrator_agent  # noqa: E402
from core.agents.archivist import archivist_agent  # noqa: E402
from core.engine.langgraph_flow import build_langgraph_flow  # noqa: E402


class DummyQueryService:
    def relations_effective_in_scene(self, scene_id: str):
        return [{"a": "e:1", "b": "e:2", "type": "ALLY"}]


@pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
def test_langgraph_flow_runs():
    llm = MockLLM()
    tools = {
        "ctx": type("Ctx", (), {"query_service": DummyQueryService(), "dry_run": True})(),
        "query_tool": lambda ctx, method, **kw: getattr(ctx.query_service, method)(**kw),
        "recorder_tool": lambda ctx, **kw: {"mode": "dry_run", **kw},
        "llm": llm,
        "narrator": narrator_agent(llm),
        "archivist": archivist_agent(llm),
    }
    graph = build_langgraph_flow(tools)
    out = graph.invoke({"intent": "Introduce a rival.", "scene_id": "scene:1"})
    assert out["plan"]["beats"] and out["draft"] and out["commit"]["mode"] == "dry_run"
