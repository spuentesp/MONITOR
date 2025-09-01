from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

try:  # Optional typing only; no runtime import dependency
    from core.ports.cache import CachePort, StagingPort  # type: ignore
    from core.ports.storage import QueryReadPort, RecorderWritePort  # type: ignore
except Exception:  # pragma: no cover
    CachePort = StagingPort = QueryReadPort = RecorderWritePort = Any  # type: ignore


@dataclass
class ToolContext:
    """Holds shared handles for tools.

    query_service: public read facade for the graph (safe to call).
    rules: optional rules/system helpers loaded from YAML (not implemented yet).
    dry_run: if True, Recorder won't persist; returns a plan/diff instead.
    """

    query_service: QueryReadPort | Any
    recorder: RecorderWritePort | Any | None = None
    rules: Any | None = None
    dry_run: bool = True
    # Optional caches (duck-typed interfaces)
    read_cache: CachePort | Any | None = None
    staging: StagingPort | Any | None = None


def query_tool(ctx: ToolContext, method: str, **kwargs) -> Any:
    """Generic, whitelisted proxy to QueryService.

    Example: query_tool(ctx, "relations_effective_in_scene", scene_id="scene:1").
    """
    allowed = {
        # Systems
        "system_usage_summary",
        "effective_system_for_universe",
        "effective_system_for_story",
        "effective_system_for_scene",
        "effective_system_for_entity",
        "effective_system_for_entity_in_story",
        # Relations
        "relation_state_history",
        "relations_effective_in_scene",
        "relation_is_active_in_scene",
        # Entities / participants
        "entities_in_scene",
        "entities_in_story",
        "entities_in_universe",
        "entities_in_story_by_role",
        "entities_in_universe_by_role",
        "participants_by_role_for_scene",
        "participants_by_role_for_story",
        # Facts / scenes
        "facts_for_scene",
        "facts_for_story",
        "scenes_for_entity",
        "scenes_in_story",
        # Catalog/listing helpers
        "stories_in_universe",
        "list_multiverses",
        "list_universes_for_multiverse",
        # Entity lookup helpers
        "entity_by_name_in_universe",
    }
    if method not in allowed:
        raise ValueError(f"Query method not allowed: {method}")
    fn: Callable[..., Any] | None = getattr(ctx.query_service, method, None)
    if not callable(fn):
        raise AttributeError(f"QueryService has no callable '{method}'")
    # Optional read-through cache
    cache_key = None
    if ctx.read_cache is not None:
        try:
            cache_key = ctx.read_cache.make_key(method, kwargs)
            cached = ctx.read_cache.get(cache_key)
            if cached is not None:
                return cached
        except Exception:
            # Cache is best-effort
            cache_key = None
    out = fn(**kwargs)
    if cache_key is not None:
        try:
            ctx.read_cache.set(cache_key, out)
        except Exception:
            pass
    return out


def rules_tool(ctx: ToolContext, action: str, **kwargs) -> dict[str, Any]:
    """Placeholder rules interpreter.

    Returns a deterministic stub resolution; to be replaced with real system logic.
    """
    return {
        "action": action,
        "inputs": kwargs,
        "result": "partial",
        "effects": [],
        "trace": ["stub:rules_tool"],
    }


def notes_tool(_: ToolContext, text: str, scope: dict[str, str] | None = None) -> dict[str, Any]:
    """Record a non-canonical note (framework-neutral stub)."""
    return {"ok": True, "text": text, "scope": scope or {}}


def recorder_tool(
    ctx: ToolContext, draft: str, deltas: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Recorder: dry-run by default; if recorder present and not dry_run, persist deltas."""
    deltas = deltas or {}
    if not ctx.dry_run and ctx.recorder is not None:
        res = ctx.recorder.commit_deltas(
            scene_id=deltas.get("scene_id"),
            facts=deltas.get("facts"),
            relation_states=deltas.get("relation_states"),
            relations=deltas.get("relations"),
            universe_id=deltas.get("universe_id"),
            new_multiverse=deltas.get("new_multiverse"),
            new_universe=deltas.get("new_universe"),
            new_arc=deltas.get("new_arc"),
            new_story=deltas.get("new_story"),
            new_scene=deltas.get("new_scene"),
            new_entities=deltas.get("new_entities"),
        )
        # Invalidate read cache after write
        try:
            if ctx.read_cache is not None:
                ctx.read_cache.clear()
        except Exception:
            pass
        return {
            "mode": "commit",
            "result": res,
            "refs": {"scene_id": deltas.get("scene_id")},
            "trace": ["recorder:persist"],
        }
    # Dry-run: stage deltas if a staging store exists
    try:
        if ctx.staging is not None:
            ctx.staging.stage(deltas)
        if ctx.read_cache is not None:
            ctx.read_cache.clear()
    except Exception:
        pass
    return {
        "mode": "dry_run",
        "draft_preview": draft[:180],
        "deltas": deltas,
        "refs": {"run_id": None, "scene_id": deltas.get("scene_id")},
        "trace": ["recorder:dry_run"],
    }
