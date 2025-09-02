from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.engine.orchestrator import run_once
from core.engine.tools import ToolContext


@dataclass
class QImpl:
    def relations_effective_in_scene(self, _sid: str):
        return []


class DummyLLM:
    def complete(self, *, system_prompt: str, messages: list[dict[str, str]], temperature: float = 0.7, max_tokens: int = 400, extra: dict[str, Any] | None = None) -> str:  # noqa: D401
        return "ok"


class RecImpl:
    def __init__(self):
        self.calls: list[dict[str, Any]] = []

    def commit_deltas(self, **payload):
        self.calls.append(payload)
        return {"ok": True, "written": {"facts": len(payload.get("facts") or [])}, "warnings": []}


def test_orchestrator_autopilot_commits():
    rec = RecImpl()
    tools = ToolContext(query_service=QImpl(), recorder=rec, dry_run=False)
    out = run_once("go", scene_id="s1", mode="autopilot", ctx=tools, llm=DummyLLM())
    assert out["commit"]["mode"] == "commit"
    assert rec.calls and rec.calls[-1].get("scene_id") == "s1"
