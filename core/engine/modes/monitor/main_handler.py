"""Main monitor mode handler coordinating all monitor operations."""
from __future__ import annotations

from typing import Dict, Any

from core.engine.monitor_parser import MonitorIntent, parse_monitor_text
from core.engine.tools import ToolContext
from core.generation.providers import select_llm_from_env
from ..state import GraphState, append_message, Message

from .crud_handlers import (
    handle_create_multiverse,
    handle_create_universe, 
    handle_save_fact,
    handle_list_multiverses,
    handle_list_universes,
    handle_list_stories,
    handle_list_scenes,
    handle_list_entities,
    handle_list_facts,
)
from .entity_handlers import (
    handle_show_entity_info,
    handle_list_enemies,
    handle_last_seen,
)
from .scene_handlers import (
    handle_end_scene,
    handle_add_scene,
    handle_modify_last_scene,
    handle_save_conversation,
    handle_show_conversation,
)
from .entity_management_handlers import (
    handle_retcon_entity,
    handle_seed_entities,
    handle_create_entity,
    handle_wizard_setup_story,
    handle_wizard_setup_scene,
)
from .setup_handlers import handle_setup_flow


def monitor_node(state: GraphState, ctx: ToolContext | None = None) -> GraphState:
    """Main monitor mode handler that routes to specific action handlers."""
    text = (state.get("text") or "").strip()
    if not text:
        append_message(state, "assistant", "No input provided to monitor.")
        state["last_mode"] = "monitor"
        return state

    # Check for wizard flows first
    wizard = (state.get("meta") or {}).get("wizard") or {}
    if wizard:
        flow = wizard.get("flow")
        if flow == "setup_story":
            return handle_wizard_setup_story(state, text, ctx)
        elif flow == "setup_scene":
            return handle_wizard_setup_scene(state, text, ctx)

    # Check for setup flow
    if text.startswith("/setup"):
        return handle_setup_flow(state, text)

    # Parse monitor intent
    intent = parse_monitor_text(text)
    action_reply = None

    # Route to specific handlers based on action
    if intent.action == "create_multiverse":
        return handle_create_multiverse(state, intent, ctx)
    elif intent.action == "create_universe":
        return handle_create_universe(state, intent, ctx)
    elif intent.action == "save_fact":
        return handle_save_fact(state, intent, ctx)
    elif intent.action in ("list_multiverses", "list_universes", "list_stories", "list_scenes", "list_entities", "list_facts"):
        if intent.action == "list_multiverses":
            return handle_list_multiverses(state, intent, ctx)
        elif intent.action == "list_universes":
            return handle_list_universes(state, intent, ctx)
        elif intent.action == "list_stories":
            return handle_list_stories(state, intent, ctx)
        elif intent.action == "list_scenes":
            return handle_list_scenes(state, intent, ctx)
        elif intent.action == "list_entities":
            return handle_list_entities(state, intent, ctx)
        elif intent.action == "list_facts":
            return handle_list_facts(state, intent, ctx)
    elif intent.action == "show_entity_info":
        return handle_show_entity_info(state, intent, ctx)
    elif intent.action == "list_enemies":
        return handle_list_enemies(state, intent, ctx)
    elif intent.action == "last_seen":
        return handle_last_seen(state, intent, ctx)
    elif intent.action == "end_scene":
        return handle_end_scene(state, intent, ctx)
    elif intent.action == "add_scene":
        return handle_add_scene(state, intent, ctx)
    elif intent.action == "modify_last_scene":
        return handle_modify_last_scene(state, intent, ctx)
    elif intent.action == "retcon_entity":
        return handle_retcon_entity(state, intent, ctx)
    elif intent.action in ("seed_pcs", "seed_npcs"):
        return handle_seed_entities(state, intent, ctx)
    elif intent.action == "create_entity":
        return handle_create_entity(state, intent, ctx)
    elif intent.action == "save_conversation":
        return handle_save_conversation(state, intent, ctx)
    elif intent.action == "show_conversation":
        return handle_show_conversation(state, intent, ctx)

    # Default LLM response if no specific action matched
    if action_reply is None:
        llm = select_llm_from_env()
        sys = (
            "Eres el Monitor, un asistente operacional. Responde breve, preciso y accionable. "
            "No escribas narrativa. Si la petición requiere ejecutar acciones reales (crear/actualizar/consultar universos, multiversos, datos), "
            "propón un plan de 2-3 pasos y confirma los datos faltantes."
        )
        msgs: list[Message] = (state.get("messages") or []) + [{"role": "user", "content": text}]
        reply = llm.complete(system_prompt=sys, messages=msgs[-8:], temperature=0.2, max_tokens=350)
    else:
        reply = action_reply

    append_message(state, "assistant", reply)
    state["last_mode"] = "monitor"
    return state
