from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from core.agents.base import Agent, AgentConfig, Session
from core.agents.narrator import narrator_agent
from core.agents.archivist import archivist_agent
from core.engine.tools import ToolContext, query_tool, rules_tool, notes_tool, recorder_tool
from core.persistence.neo4j_repo import Neo4jRepo
from core.persistence.queries import QueryService
from core.engine.langgraph_flow import select_engine_backend
from core.persistence.recorder import RecorderService


@dataclass
class OrchestratorConfig:
    mode: str = "copilot"  # or "autopilot"
    style: Optional[str] = None


class Orchestrator:
    """Minimal framework-neutral orchestrator.

    This is a thin placeholder until LangGraph wiring; it demonstrates tool usage.
    """

    def __init__(self, llm: Any, tools: ToolContext, config: Optional[OrchestratorConfig] = None):
        self.tools = tools
        self.config = config or OrchestratorConfig()
        self.narrator: Agent = narrator_agent(llm)
        self.archivist: Agent = archivist_agent(llm)
        self.session = Session(primary=self.narrator)

    def step(self, user_intent: str, scene_id: Optional[str] = None) -> Dict[str, Any]:
        # Director (stub): interpret intent as goals
        plan = {"beats": [user_intent], "risks": [], "assumptions": []}

        # Librarian: retrieve context (stub via QueryService where possible)
        evidence = []
        if scene_id:
            try:
                effective = query_tool(self.tools, "relations_effective_in_scene", scene_id=scene_id)
                evidence.append({"relations": effective})
            except Exception:
                pass

        # Steward: validate (stub)
        validation = {"ok": True, "warnings": []}

        # Narrator: draft
        self.session.user(user_intent)
        draft = self.session.step()

        # Critic: score (stub)
        critique = {"coherence": 0.9, "length": len(draft)}

        # Archivist: summarize
        summary = self.archivist.act([{"role": "user", "content": draft}])

        # Recorder: dry-run commit plan
        commit = recorder_tool(self.tools, draft=draft, deltas={"scene_id": scene_id})

        return {
            "plan": plan,
            "evidence": evidence,
            "validation": validation,
            "draft": draft,
            "critique": critique,
            "summary": summary,
            "commit": commit,
        }


def build_live_tools(dry_run: bool = True) -> ToolContext:
    """Construct a ToolContext backed by the live Neo4j graph using env vars."""
    repo = Neo4jRepo().connect()
    qs = QueryService(repo)
    recorder = RecorderService(repo)
    return ToolContext(query_service=qs, recorder=recorder, dry_run=dry_run)


def run_once(user_intent: str, scene_id: Optional[str] = None, mode: str = "copilot") -> Dict[str, Any]:
    """Convenience function to run a single step against the live graph.

    Chooses backend by env MONITOR_ENGINE_BACKEND=(inmemory|langgraph); defaults to inmemory.
    In copilot, Recorder is skipped (pause) if MONITOR_COPILOT_PAUSE is truthy.
    """
    tools = build_live_tools(dry_run=(mode != "autopilot"))
    backend = select_engine_backend()
    from core.generation.mock_llm import MockLLM  # local import to avoid hard dep
    if backend == "langgraph":
        try:
            from core.engine.langgraph_flow import build_langgraph_flow
        except Exception:
            backend = "inmemory"
    if backend == "langgraph":
        # Build agents/tools package for langgraph_flow
        tools_pkg = {
            "ctx": tools,
            "query_tool": query_tool,
            "recorder_tool": recorder_tool,
            "llm": MockLLM(),
            "narrator": narrator_agent(MockLLM()),
            "archivist": archivist_agent(MockLLM()),
        }
        graph = build_langgraph_flow(tools_pkg)
        out = graph.invoke({"intent": user_intent, "scene_id": scene_id})
        return out
    # fallback to in-memory orchestrator
    orch = Orchestrator(llm=MockLLM(), tools=tools, config=OrchestratorConfig(mode=mode))
    return orch.step(user_intent=user_intent, scene_id=scene_id)
