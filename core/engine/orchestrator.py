from __future__ import annotations

import os
from typing import Any

from core.agents.archivist import archivist_agent
from core.agents.narrator import narrator_agent
from core.agents.director import director_agent
from core.agents.librarian import librarian_agent as librarian_llm_agent
from core.agents.steward import steward_agent as steward_llm_agent
from core.agents.critic import critic_agent
from core.engine.cache import ReadThroughCache, StagingStore
from core.engine.langgraph_flow import select_engine_backend
from queue import Queue
from core.engine.autocommit import AutoCommitWorker

# Module-level singletons to avoid spawning a worker per request
_AUTOCOMMIT_WORKER: AutoCommitWorker | None = None
_AUTOCOMMIT_QUEUE: Queue | None = None
_IDEMPOTENCY_SET: set[str] = set()
from core.engine.tools import ToolContext, query_tool, recorder_tool
from core.persistence.neo4j_repo import Neo4jRepo
from core.persistence.queries import QueryService
from core.persistence.recorder import RecorderService

try:
    from core.engine.cache_redis import RedisReadThroughCache, RedisStagingStore  # type: ignore
except Exception:  # pragma: no cover
    RedisReadThroughCache = None  # type: ignore
    RedisStagingStore = None  # type: ignore



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
    # Optional async autocommit worker
    autocommit_enabled = os.getenv("MONITOR_AUTOCOMMIT", "0") in ("1", "true", "True")
    autocommit_q = None
    worker = None
    if autocommit_enabled and recorder is not None:
        global _AUTOCOMMIT_WORKER, _AUTOCOMMIT_QUEUE, _IDEMPOTENCY_SET
        if _AUTOCOMMIT_WORKER is None or _AUTOCOMMIT_QUEUE is None:
            _AUTOCOMMIT_QUEUE = Queue(maxsize=1024)
            _AUTOCOMMIT_WORKER = AutoCommitWorker(
                queue=_AUTOCOMMIT_QUEUE,
                recorder=recorder,
                read_cache=read_cache,
                idempotency=_IDEMPOTENCY_SET,
            )
            try:
                _AUTOCOMMIT_WORKER.start()
            except Exception:
                _AUTOCOMMIT_WORKER = None
                _AUTOCOMMIT_QUEUE = None
                autocommit_enabled = False
        autocommit_q = _AUTOCOMMIT_QUEUE
        worker = _AUTOCOMMIT_WORKER
    return ToolContext(
        query_service=qs,
        recorder=recorder,
        dry_run=dry_run,
        read_cache=read_cache,
        staging=staging,
        autocommit_enabled=autocommit_enabled,
        autocommit_queue=autocommit_q,
        autocommit_worker=worker,
    idempotency=_IDEMPOTENCY_SET if autocommit_enabled else None,
    )


def autocommit_stats() -> dict[str, Any]:
    """Return current AutoCommit worker stats if running."""
    try:
        if _AUTOCOMMIT_WORKER is not None:
            return {"enabled": True, **_AUTOCOMMIT_WORKER.get_stats()}
    except Exception:
        pass
    return {"enabled": False}


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
    user_intent: str,
    scene_id: str | None = None,
    mode: str = "copilot",
    *,
    ctx: ToolContext | None = None,
    llm: Any | None = None,
) -> dict[str, Any]:
    """Convenience function to run a single step against the live graph.

    Chooses backend by env MONITOR_ENGINE_BACKEND=(inmemory|langgraph); defaults to langgraph.
    In copilot, Recorder can pause if MONITOR_COPILOT_PAUSE is truthy.
    """
    tools = ctx or build_live_tools(dry_run=(mode != "autopilot"))
    from core.generation.providers import select_llm_from_env

    llm = llm or select_llm_from_env()
    backend = select_engine_backend()
    try:
        if backend == "langgraph":
            from core.engine.langgraph_flow import build_langgraph_flow
            # Build agents/tools package for langgraph_flow
            tools_pkg = {
                "ctx": tools,
                "query_tool": query_tool,
                "recorder_tool": recorder_tool,
                "llm": llm,
                "narrator": narrator_agent(llm),
                "archivist": archivist_agent(llm),
                # Additional LLM agents for flow
                "director": director_agent(llm),
                "librarian": librarian_llm_agent(llm),
                "steward": steward_llm_agent(llm),
                "critic": critic_agent(llm),
            }
            graph = build_langgraph_flow(tools_pkg)
            out = graph.invoke({"intent": user_intent, "scene_id": scene_id})
            return out
    except Exception:
        # Fall through to minimal path if langgraph is unavailable
        pass
    # Minimal fallback: narrator -> archivist -> recorder
    draft = narrator_agent(llm).act([{ "role": "user", "content": user_intent }])
    summary = archivist_agent(llm).act([{ "role": "user", "content": draft }])
    commit = recorder_tool(tools, draft=draft, deltas={"scene_id": scene_id})
    return {"draft": draft, "summary": summary, "commit": commit}
