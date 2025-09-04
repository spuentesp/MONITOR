"""CRUD operation handlers for monitor mode."""
from __future__ import annotations

from core.engine.monitor_parser import MonitorIntent
from core.engine.tools import query_tool
from ..state import GraphState, append_message, gen_id
from .utils import commit_deltas


def handle_create_multiverse(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle creating a new multiverse."""
    new_mv = {
        "id": intent.id,
        "name": intent.name,
        "omniverse_id": state.get("omniverse_id"),
    }
    deltas = {"new_multiverse": new_mv, "_draft": f"Create multiverse {intent.name}"}
    res = commit_deltas(ctx, deltas)
    action_reply = f"Multiverso creado (modo={res.get('mode')})."
    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    return state


def handle_create_universe(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle creating a new universe."""
    mv_id = intent.multiverse_id or state.get("multiverse_id")
    universe_id = state.get("universe_id")
    new_u = {
        "id": intent.id,
        "name": intent.name,
        "multiverse_id": mv_id,
        "description": None,
    }
    res = commit_deltas(
        ctx,
        {
            "new_universe": new_u,
            "universe_id": universe_id,
            "_draft": f"Crear universo {intent.id or '(auto-id)'}",
        }
    )
    action_reply = f"Universo creado (modo={res.get('mode')})."
    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    return state


def handle_save_fact(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle saving a fact to the current scene/universe."""
    universe_id = state.get("universe_id")
    desc = (intent.description or "").strip()
    fact = {"description": desc or "(sin descripción)", "universe_id": universe_id}
    if intent.scene_id or state.get("scene_id"):
        fact["occurs_in"] = intent.scene_id or state.get("scene_id")
    res = commit_deltas(ctx, {"facts": [fact], "universe_id": universe_id, "_draft": desc[:120]})
    action_reply = f"Hecho guardado (modo={res.get('mode')})."
    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    return state


def handle_list_multiverses(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle listing all available multiverses."""
    try:
        rows = query_tool(ctx, "list_multiverses") if ctx else []
        if not rows:
            action_reply = "No multiverses found."
        else:
            lines = [f"- {r.get('name') or r.get('id')} ({r.get('id')})" for r in rows]
            action_reply = "Multiverses:\n" + "\n".join(lines)
    except Exception as e:
        action_reply = f"Error listing multiverses: {e}"
    
    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    return state


def handle_list_universes(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle listing universes in a multiverse."""
    mv = intent.multiverse_id or state.get("multiverse_id")
    if not mv:
        action_reply = "Please specify a multiverse id (e.g., multiverse mv:demo)."
    else:
        try:
            rows = (
                query_tool(ctx, "list_universes_for_multiverse", multiverse_id=mv)
                if ctx
                else []
            )
            if not rows:
                action_reply = f"No universes found in {mv}."
            else:
                lines = [f"- {r.get('name') or r.get('id')} ({r.get('id')})" for r in rows]
                action_reply = f"Universes in {mv}:\n" + "\n".join(lines)
        except Exception as e:
            action_reply = f"Error listing universes: {e}"
    
    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    return state


def handle_list_stories(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle listing stories in a universe."""
    uid = intent.universe_id or state.get("universe_id")
    if not uid:
        action_reply = "Please specify a universe id (e.g., universe u:demo)."
    else:
        try:
            rows = query_tool(ctx, "stories_in_universe", universe_id=uid) if ctx else []
            if not rows:
                action_reply = f"No stories found in {uid}."
            else:
                lines = [
                    f"- {r.get('title') or r.get('id')} (id={r.get('id')}, arc={r.get('arc_id') or '-'}, seq={r.get('sequence_index')})"
                    for r in rows
                ]
                action_reply = f"Stories in {uid}:\n" + "\n".join(lines)
        except Exception as e:
            action_reply = f"Error listing stories: {e}"
    
    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    return state
