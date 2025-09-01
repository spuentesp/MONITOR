from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from core.engine.cache import ReadThroughCache, StagingStore


@dataclass
class ToolContext:
    """Holds shared handles for tools.

    query_service: public read facade for the graph (safe to call).
    rules: optional rules/system helpers loaded from YAML (not implemented yet).
    dry_run: if True, Recorder won't persist; returns a plan/diff instead.
    """

    query_service: Any
    recorder: Optional[Any] = None
    rules: Optional[Any] = None
    dry_run: bool = True
    # Optional caches (duck-typed interfaces)
    read_cache: Optional[Any] = None
    staging: Optional[Any] = None


def query_tool(ctx: ToolContext, method: str, **kwargs) -> Any:
    """Generic, whitelisted proxy to QueryService.

    Example: query_tool(ctx, "relations_effective_in_scene", scene_id="scene:1").
    """
    allowed = {
        "system_usage_summary",
        "effective_system_for_universe",
        "effective_system_for_story",
        "effective_system_for_scene",
        "effective_system_for_entity",
        "effective_system_for_entity_in_story",
        "relation_state_history",
        "relations_effective_in_scene",
        "relation_is_active_in_scene",
    }
    if method not in allowed:
        raise ValueError(f"Query method not allowed: {method}")
    fn: Optional[Callable[..., Any]] = getattr(ctx.query_service, method, None)
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


def rules_tool(ctx: ToolContext, action: str, **kwargs) -> Dict[str, Any]:
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


def notes_tool(_: ToolContext, text: str, scope: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Record a non-canonical note (framework-neutral stub)."""
    return {"ok": True, "text": text, "scope": scope or {}}


def recorder_tool(ctx: ToolContext, draft: str, deltas: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
