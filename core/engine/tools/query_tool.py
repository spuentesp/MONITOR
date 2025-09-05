from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .tool_context import ToolContext


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
        "list_universes",
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
    if cache_key is not None and ctx.read_cache is not None:
        try:
            ctx.read_cache.set(cache_key, out)
        except Exception:
            pass
    return out


def rules_tool(ctx: ToolContext, action: str, **kwargs) -> dict[str, Any]:
    """Minimal rules evaluator supporting a few simple checks.

    Supported actions:
      - forbid_relation(type, a, b): returns violation if relation exists/effective.
      - require_role_in_scene(role, scene_id): returns violation if no participant with role.
      - max_participants(scene_id, limit): returns violation if participants > limit.
    """
    effects: list[dict[str, Any]] = []
    violations: list[str] = []
    trace: list[str] = ["rules:minimal"]
    try:
        if action == "forbid_relation":
            rtype = kwargs["type"]
            a = kwargs["a"]
            b = kwargs["b"]
            try:
                active = bool(ctx.query_service.relation_is_active_in_scene(a=a, b=b, type=rtype))
            except Exception:
                active = False
            if active:
                violations.append(f"forbid_relation: {rtype} between {a} and {b} is active")
        elif action == "require_role_in_scene":
            role = kwargs["role"]
            scene_id = kwargs["scene_id"]
            try:
                participants = ctx.query_service.participants_by_role_for_scene(scene_id, role=role)
            except Exception:
                participants = []
            if not participants:
                violations.append(
                    f"require_role_in_scene: no participants with role '{role}' in scene {scene_id}"
                )
        elif action == "max_participants":
            scene_id = kwargs["scene_id"]
            limit = int(kwargs["limit"])
            try:
                # Get all entities in scene
                all_entities = ctx.query_service.entities_in_scene(scene_id) or []
            except Exception:
                all_entities = []
            if len(all_entities) > limit:
                violations.append(
                    f"max_participants: scene {scene_id} has {len(all_entities)} > {limit}"
                )
        else:
            violations.append(f"rules_tool: unknown action '{action}'")
    except Exception as e:
        violations.append(f"rules_tool error: {e}")

    # Add result field for backward compatibility with tests
    result = "violations" if violations else "ok"
    return {"result": result, "effects": effects, "violations": violations, "trace": trace}
