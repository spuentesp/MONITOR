from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

from core.agents.archivist import archivist_agent
from core.agents.base import Agent, Session
from core.agents.narrator import narrator_agent
from core.engine.cache import ReadThroughCache, StagingStore
from core.engine.langgraph_flow import select_engine_backend
from core.engine.librarian import LibrarianService
from core.engine.steward import StewardService
from core.engine.tools import ToolContext, query_tool, recorder_tool
from core.persistence.neo4j_repo import Neo4jRepo
from core.persistence.queries import QueryService
from core.persistence.recorder import RecorderService

try:
    from core.engine.cache_redis import RedisReadThroughCache, RedisStagingStore  # type: ignore
except Exception:  # pragma: no cover
    RedisReadThroughCache = None  # type: ignore
    RedisStagingStore = None  # type: ignore


@dataclass
class OrchestratorConfig:
    mode: str = "copilot"  # or "autopilot"
    style: str | None = None


class Orchestrator:
    """Minimal framework-neutral orchestrator.

    This is a thin placeholder until LangGraph wiring; it demonstrates tool usage.
    """

    def __init__(self, llm: Any, tools: ToolContext, config: OrchestratorConfig | None = None):
        self.tools = tools
        self.config = config or OrchestratorConfig()
        self.narrator: Agent = narrator_agent(llm)
        self.archivist: Agent = archivist_agent(llm)
        self.session = Session(primary=self.narrator)
        self.librarian_svc = LibrarianService(self.tools.query_service)
        self.steward_svc = StewardService(self.tools.query_service)

    def _build_context(self, scene_id: str | None) -> str:
        if not scene_id:
            return ""
        return self.librarian_svc.scene_brief(scene_id)

    def step(self, user_intent: str, scene_id: str | None = None) -> dict[str, Any]:
        # Director (stub): interpret intent as goals
        plan = {"beats": [user_intent], "risks": [], "assumptions": []}

        # Librarian: retrieve context (stub via QueryService where possible)
        evidence = []
        if scene_id:
            try:
                effective = query_tool(
                    self.tools, "relations_effective_in_scene", scene_id=scene_id
                )
                evidence.append({"relations": effective})
            except Exception:
                pass

        # Steward: validate (stub)
        validation = {"ok": True, "warnings": []}

        # Narrator: draft (RAG-style context injection as ephemeral system message)
        context_msg = self._build_context(scene_id)
        messages = list(self.session.history)
        if context_msg:
            messages.append({"role": "system", "content": context_msg})
        messages.append({"role": "user", "content": user_intent})
        draft = self.narrator.act(messages)
        # Update session history without persisting the ephemeral system context
        self.session.user(user_intent)
        self.session.history.append({"role": "assistant", "content": draft})

        # Critic: score (stub)
        critique = {"coherence": 0.9, "length": len(draft)}

        # Archivist: summarize
        summary = self.archivist.act([{"role": "user", "content": draft}])

        # Steward: pre-commit validation; commit only if no errors
        proposed = {"scene_id": scene_id}
        ok, warns, errs = self.steward_svc.validate(proposed)
        validation = {"ok": ok, "warnings": warns, "errors": errs}
        if ok:
            commit = recorder_tool(self.tools, draft=draft, deltas=proposed)
        else:
            commit = {"mode": "blocked", "reason": "steward_errors", "errors": errs}

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
    """Construct a ToolContext backed by the live Neo4j graph using env vars, with optional caching.

    Falls back to a demo in-memory stub when Neo4j connection/env is missing so Streamlit can run.
    """
    from core.services.query_service import QueryServiceFacade
    from core.services.recorder_service import RecorderServiceFacade

    try:
        repo = Neo4jRepo().connect()
        qs = QueryServiceFacade(QueryService(repo))
        recorder = RecorderServiceFacade(RecorderService(repo))
    except Exception:
        # Demo fallback: minimal stubs that satisfy allowed query and recorder operations
        class _QDemo:
            def system_usage_summary(self, *_a, **_k):
                return {}

            def effective_system_for_universe(self, *_a, **_k):
                return {}

            def effective_system_for_story(self, *_a, **_k):
                return {}

            def effective_system_for_scene(self, *_a, **_k):
                return {}

            def effective_system_for_entity(self, *_a, **_k):
                return {}

            def effective_system_for_entity_in_story(self, *_a, **_k):
                return {}

            def relation_state_history(self, *_a, **_k):
                return []

            def relations_effective_in_scene(self, *_a, **_k):
                return []

            def relation_is_active_in_scene(self, *_a, **_k):
                return False

            # New monitor-friendly read methods (stubs)
            def entities_in_scene(self, *_a, **_k):
                return []

            def entities_in_story(self, *_a, **_k):
                return []

            def entities_in_universe(self, *_a, **_k):
                return []

            def entities_in_universe_by_role(self, *_a, **_k):
                return []

            def participants_by_role_for_scene(self, *_a, **_k):
                return []

            def participants_by_role_for_story(self, *_a, **_k):
                return []

            def facts_for_scene(self, *_a, **_k):
                return []

            def facts_for_story(self, *_a, **_k):
                return []

            def scenes_for_entity(self, *_a, **_k):
                return []

            def scenes_in_story(self, *_a, **_k):
                return []

            def stories_in_universe(self, *_a, **_k):
                return []

            def list_multiverses(self, *_a, **_k):
                return []

            def list_universes_for_multiverse(self, *_a, **_k):
                return []

            def entity_by_name_in_universe(self, *_a, **_k):
                return None

        class _RDemo:
            def commit_deltas(self, **_payload):
                return {"ok": True, "written": {}, "warnings": []}

        qs = QueryServiceFacade(_QDemo())
        recorder = RecorderServiceFacade(_RDemo())
    backend = os.getenv("MONITOR_CACHE_BACKEND", "").lower()  # "redis" or ""
    ttl = float(os.getenv("MONITOR_CACHE_TTL", "60"))
    if backend == "redis" and RedisReadThroughCache and RedisStagingStore:
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        read_cache = RedisReadThroughCache(url=url, ttl_seconds=ttl)
        staging = RedisStagingStore(url=url, list_key="monitor:staging", daily=True)
    else:
        read_cache = ReadThroughCache(capacity=512, ttl_seconds=ttl)
        staging = StagingStore()
    return ToolContext(
        query_service=qs, recorder=recorder, dry_run=dry_run, read_cache=read_cache, staging=staging
    )


def flush_staging(ctx: ToolContext) -> dict[str, Any]:
    """Flush staged deltas to the graph and clear caches."""
    if not ctx.recorder or not ctx.staging:
        return {"ok": False, "error": "recorder/staging not configured"}
    res = ctx.staging.flush(ctx.recorder, clear_after=True)
    try:
        if ctx.read_cache is not None:
            ctx.read_cache.clear()
    except Exception:
        pass
    return res


def run_once(
    user_intent: str, scene_id: str | None = None, mode: str = "copilot"
) -> dict[str, Any]:
    """Convenience function to run a single step against the live graph.

    Chooses backend by env MONITOR_ENGINE_BACKEND=(inmemory|langgraph); defaults to inmemory.
    In copilot, Recorder is skipped (pause) if MONITOR_COPILOT_PAUSE is truthy.
    """
    tools = build_live_tools(dry_run=(mode != "autopilot"))
    backend = select_engine_backend()
    from core.generation.providers import select_llm_from_env

    llm = select_llm_from_env()
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
            "llm": llm,
            "narrator": narrator_agent(llm),
            "archivist": archivist_agent(llm),
        }
        graph = build_langgraph_flow(tools_pkg)
        out = graph.invoke({"intent": user_intent, "scene_id": scene_id})
        return out
    # fallback to in-memory orchestrator
    orch = Orchestrator(llm=llm, tools=tools, config=OrchestratorConfig(mode=mode))
    return orch.step(user_intent=user_intent, scene_id=scene_id)
