"""Entity and relationship query handlers for monitor mode."""

from __future__ import annotations

from core.engine.monitor_parser import MonitorIntent
from core.engine.tools import query_tool

from ..state import GraphState, append_message


def handle_show_entity_info(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle showing detailed information about an entity."""
    uid = intent.universe_id or state.get("universe_id")
    name = (intent.entity_name or "").strip()
    if not uid or not name:
        action_reply = "Please provide an entity name and universe (e.g., show 'Tony Stark' in universe u:demo)."
    else:
        try:
            ent = (
                query_tool(ctx, "entity_by_name_in_universe", universe_id=uid, name=name)
                if ctx
                else None
            )
            if not ent:
                action_reply = f"Entity '{name}' not found in {uid}."
            else:
                # basic appearances and facts
                scenes = query_tool(ctx, "scenes_for_entity", entity_id=ent["id"]) if ctx else []
                info = [f"Entity: {ent['name']} (id={ent['id']}, type={ent.get('type') or '-'})"]
                if scenes:
                    info.append("Appears in scenes:")
                    info.extend(
                        [
                            f"  - story={s.get('story_id')}, scene={s.get('scene_id')}, seq={s.get('sequence_index')}"
                            for s in scenes
                        ]
                    )
                action_reply = "\n".join(info)
        except Exception as e:
            action_reply = f"Error fetching entity info: {e}"

    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    return state


def handle_list_enemies(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle listing enemies of a character in a universe."""
    uid = intent.universe_id or state.get("universe_id")
    name = (intent.entity_name or "").strip()
    if not uid or not name:
        action_reply = "Please provide a character name and universe (e.g., enemies of 'Rogue' in universe u:demo)."
    else:
        try:
            ent = (
                query_tool(ctx, "entity_by_name_in_universe", universe_id=uid, name=name)
                if ctx
                else None
            )
            if not ent:
                action_reply = f"Entity '{name}' not found in {uid}."
            else:
                # MVP heuristic: list entities with role='ENEMY' in universe
                rows = (
                    query_tool(ctx, "entities_in_universe_by_role", universe_id=uid, role="ENEMY")
                    if ctx
                    else []
                )
                lines = [f"- {r.get('name')} ({r.get('id')})" for r in rows] if rows else []
                action_reply = (
                    (f"Enemies in {uid}:\n" + "\n".join(lines))
                    if lines
                    else f"No enemies found in {uid}."
                )
        except Exception as e:
            action_reply = f"Error listing enemies: {e}"

    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    return state


def handle_last_seen(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle finding when a character was last seen."""
    uid = intent.universe_id or state.get("universe_id")
    name = (intent.entity_name or "").strip()
    if not uid or not name:
        action_reply = "Please provide a character name and universe (e.g., last time they saw 'Deadpool' in universe u:demo)."
    else:
        try:
            ent = (
                query_tool(ctx, "entity_by_name_in_universe", universe_id=uid, name=name)
                if ctx
                else None
            )
            if not ent:
                action_reply = f"Entity '{name}' not found in {uid}."
            else:
                # Find scenes for entity then pick the highest sequence index per story
                scenes = query_tool(ctx, "scenes_for_entity", entity_id=ent["id"]) if ctx else []
                if not scenes:
                    action_reply = f"No appearances found for {name}."
                else:
                    # Simple sort by (story_id, sequence_index)
                    scenes_sorted = sorted(
                        scenes,
                        key=lambda s: (s.get("story_id"), s.get("sequence_index") or -1),
                    )
                    last = scenes_sorted[-1]
                    action_reply = f"Last seen in story={last.get('story_id')}, scene={last.get('scene_id')} (seq={last.get('sequence_index')})."
        except Exception as e:
            action_reply = f"Error computing last seen: {e}"

    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    return state
