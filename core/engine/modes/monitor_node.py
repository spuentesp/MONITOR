"""Monitor node for operational responses and system management."""
from __future__ import annotations

from core.engine.monitor_parser import parse_monitor_intent

from .constants import CMD_HELP, HELP_TEXT
from .graph_state import GraphState, append_message, generate_id
from .monitor_actions import commit_deltas, generate_llm_response
from .wizard_flows import handle_start_story_wizard, handle_setup_universe_wizard


def monitor_node(state: GraphState) -> GraphState:
    """Respond as Monitor (operational mode).
    
    Handles system commands, data operations, and multi-turn wizards.
    """
    text = state.get("input", "").strip()
    
    # Handle help requests
    if state.get("_help") or CMD_HELP.match(text):
        append_message(state, "assistant", HELP_TEXT)
        state["last_mode"] = "monitor"
        return state
    
    # Parse operational intent
    intent = parse_monitor_intent(text)
    action_reply: str | None = None
    
    if intent:
        action_reply = _handle_intent(state, intent)
    
    # Use LLM fallback if no specific action
    if action_reply is None:
        action_reply = generate_llm_response(state, text)
    
    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    
    return state


def _handle_intent(state: GraphState, intent: Any) -> str | None:
    """Handle specific parsed intents."""
    if intent.action == "start_story":
        handle_start_story_wizard(state, intent)
        return None  # Wizard handles the response
    
    if intent.action == "setup_universe":
        handle_setup_universe_wizard(state, intent)
        return None  # Wizard handles the response
    
    if intent.action == "create_multiverse":
        return _create_multiverse(state, intent)
    
    if intent.action == "create_universe":
        return _create_universe(state, intent)
    
    # Add more intent handlers as needed
    return None


def _create_multiverse(state: GraphState, intent: Any) -> str:
    """Create a new multiverse."""
    new_mv = {
        "id": intent.id,
        "name": intent.name,
        "omniverse_id": state.get("omniverse_id"),
    }
    
    res = commit_deltas(state, {
        "new_multiverse": new_mv, 
        "_draft": f"Crear multiverso {intent.id or '(auto-id)'}"
    })
    
    return f"Multiverso creado (modo={res.get('mode')})."


def _create_universe(state: GraphState, intent: Any) -> str:
    """Create a new universe."""
    mv_id = intent.multiverse_id or state.get("multiverse_id")
    
    new_u = {
        "id": intent.id,
        "name": intent.name,
        "multiverse_id": mv_id,
        "description": None,
    }
    
    res = commit_deltas(state, {
        "new_universe": new_u,
        "universe_id": intent.id,
        "_draft": f"Crear universo {intent.id or '(auto-id)'}"
    })
    
    return f"Universo creado (modo={res.get('mode')})."
