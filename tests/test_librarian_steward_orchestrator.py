from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.engine.librarian import LibrarianService
from core.engine.orchestrator import Orchestrator, OrchestratorConfig
from core.engine.steward import StewardService
from core.engine.tools import ToolContext


@dataclass
class QImpl:
    def relations_effective_in_scene(self, _sid: str):
        return [{"a": "e1", "b": "e2", "type": "ally"}]

    def entities_in_scene(self, _sid: str):
        return [{"id": "e1"}, {"id": "e2"}]

    def facts_for_scene(self, _sid: str):
        return [{"description": "d1"}, {"description": "d2"}]


class DummyLLM:
    def complete(self, *, system_prompt: str, messages: list[dict[str, str]], temperature: float = 0.7, max_tokens: int = 400, extra: dict[str, Any] | None = None) -> str:  # noqa: D401
        return f"ACK: {messages[-1]['content']}"


def test_librarian_scene_brief():
    lb = LibrarianService(QImpl())
    out = lb.scene_brief("s1")
    assert "Context for scene s1" in out and "Relations:" in out and "Facts:" in out


def test_steward_validate():
    st = StewardService(QImpl())
    ok, warns, errs = st.validate({"scene_id": "s1", "facts": [{"participants": [{"entity_id": "e1", "role": "pc"}]}]})
    assert ok and isinstance(warns, list) and isinstance(errs, list)


def test_orchestrator_step_smoke():
    tools = ToolContext(query_service=QImpl())
    orch = Orchestrator(llm=DummyLLM(), tools=tools, config=OrchestratorConfig(mode="copilot"))
    out = orch.step("hello", scene_id="s1")
    assert out["draft"].startswith("ACK:") and "commit" in out
