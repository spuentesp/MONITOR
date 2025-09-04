"""Entity creation and management handlers for monitor mode."""
from __future__ import annotations

import re
from typing import Dict, Any

from core.engine.monitor_parser import MonitorIntent
from core.engine.tools import query_tool
from core.engine.attribute_extractor import distill_entity_attributes
from ..state import GraphState, append_message, gen_id
from .utils import commit_deltas


def handle_retcon_entity(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle retconning (removing/changing) an entity."""
    uid = state.get("universe_id")
    name = (intent.entity_name or "").strip()
    repl = (intent.replacement_name or "").strip() or None
    if not uid or not name:
        action_reply = "Please specify an entity to retcon and current universe."
    else:
        try:
            # Minimal retcon: write a Fact documenting the change; deep graph surgery is a larger follow-up.
            desc = f"RETCON: {name} {'→ ' + repl if repl else 'removed from continuity'}."
            res = commit_deltas(ctx, {
                    "facts": [{"description": desc, "universe_id": uid}],
                    "_draft": desc[:120],
                })
            action_reply = f"Retcon noted (mode={res.get('mode')})."
        except Exception as e:
            action_reply = f"Error retconning entity: {e}"
    
    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    return state


def handle_seed_entities(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle seeding PCs or NPCs."""
    uid = state.get("universe_id")
    if not uid:
        action_reply = "Please set a universe_id first."
    else:
        names = intent.names or []
        if not names:
            action_reply = (
                'Provide one or more names in quotes, e.g., seed pcs "Alice", "Bob".'
            )
        else:
            # Assign IDs so we can link to the current scene if present
            new_entities = [
                {
                    "id": gen_id("entity"),
                    "name": n,
                    "type": intent.kind,
                    "universe_id": uid,
                }
                for n in names
            ]
            deltas = {
                "new_entities": new_entities,
                "universe_id": uid,
                "_draft": f"Seed {intent.kind or 'entity'}s: {', '.join(names[:3])}",
            }
            if state.get("scene_id"):
                deltas["new_scene"] = {
                    "id": state["scene_id"],
                    "participants": [e["id"] for e in new_entities],
                }
            res = commit_deltas(ctx, deltas)
            action_reply = f"Seeded {len(new_entities)} {intent.kind or 'entity'}(s) (mode={res.get('mode')})."
    
    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    return state


def handle_create_entity(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle creating a new entity."""
    uid = state.get("universe_id")
    if not uid:
        action_reply = "Please set a universe_id first."
    else:
        if not intent.name:
            action_reply = (
                'Provide a name, e.g., create character "Logan" as npc type mutant.'
            )
        else:
            # Distill attributes from description (if provided via 'with ...' in parser in the future) or use entity_type/kind
            attrs = (
                distill_entity_attributes(intent.description) if intent.description else {}
            )
            if intent.entity_type:
                attrs.setdefault("type", intent.entity_type)
            e_id = gen_id("entity")
            new_e = {
                "id": e_id,
                "name": intent.name,
                "type": intent.kind or attrs.get("type"),
                "universe_id": uid,
                "attributes": (attrs or None),
            }
            deltas = {
                "new_entities": [new_e],
                "universe_id": uid,
                "_draft": f"Create entity {intent.name}",
            }
            # Optional linking: story/scene assignment if present in state or intent
            story_id = intent.story_id or state.get("story_id")
            scene_id = intent.scene_id or state.get("scene_id")
            if scene_id:
                deltas["new_scene"] = {"id": scene_id, "participants": [e_id]}
            res = commit_deltas(ctx, deltas)
            action_reply = f"Entity created (mode={res.get('mode')})."
    
    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    return state


def handle_wizard_setup_story(state: GraphState, text: str, ctx=None) -> GraphState:
    """Handle wizard flow for setting up a story."""
    wizard = (state.get("meta") or {}).get("wizard") or {}
    
    m = re.search(
        r"(?:nombre|name)\s+\"([^\"]+)\"|'([^']+)'", text, flags=re.IGNORECASE
    )
    title = (m.group(1) or m.group(2)) if m else None
    if not title:
        append_message(
            state,
            "assistant",
            'Por favor indica el nombre de la historia (p.ej. nombre "Prólogo").',
        )
        state["last_mode"] = "monitor"
        return state
    
    st_id = gen_id("story")
    u_id = wizard.get("universe_id") or state.get("universe_id")
    new_story = {"id": st_id, "title": title, "universe_id": u_id}
    res = commit_deltas(ctx, {
            "new_story": new_story,
            "universe_id": u_id,
            "_draft": f"Crear historia {title}",
        })
    # Move to scene setup
    meta = state.get("meta") or {}
    meta["wizard"] = {"flow": "setup_scene", "universe_id": u_id, "story_id": st_id}
    state["meta"] = meta
    append_message(
        state,
        "assistant",
        f'Historia creada (modo={res.get("mode")}). Indica el nombre de la escena inicial (p.ej. nombre "Escena 1: Llegada").',
    )
    state["last_mode"] = "monitor"
    return state


def handle_wizard_setup_scene(state: GraphState, text: str, ctx=None) -> GraphState:
    """Handle wizard flow for setting up a scene."""
    from core.generation.providers import select_llm_from_env
    from core.agents.narrator import narrator_agent
    
    wizard = (state.get("meta") or {}).get("wizard") or {}
    
    m = re.search(
        r"(?:nombre|name)\s+\"([^\"]+)\"|'([^']+)'", text, flags=re.IGNORECASE
    )
    title = (m.group(1) or m.group(2)) if m else None
    if not title:
        append_message(
            state,
            "assistant",
            'Por favor indica el nombre de la escena (p.ej. nombre "Escena 1").',
        )
        state["last_mode"] = "monitor"
        return state
    
    sc_id = gen_id("scene")
    story_id = wizard.get("story_id")
    new_scene = {"id": sc_id, "title": title, "story_id": story_id}
    res = commit_deltas(ctx, {"new_scene": new_scene, "_draft": f"Crear escena {title}"})
    state["scene_id"] = sc_id
    
    # Generate initial narrative and save as fact
    try:
        llm = select_llm_from_env()
        agent = narrator_agent(llm)
        primer = agent.act(
            [
                {
                    "role": "system",
                    "content": "Genera un inicio breve (3-5 frases) para la primera escena dada su premisa/título.",
                },
                {
                    "role": "user",
                    "content": f"Escena: {title}. Presenta un gancho inmersivo.",
                },
            ]
        )
        commit_deltas(ctx, {
                "facts": [{"description": primer, "occurs_in": sc_id}],
                "_draft": primer[:120],
            })
    except Exception:
        pass
    
    # Close wizard
    meta = state.get("meta") or {}
    meta.pop("wizard", None)
    state["meta"] = meta
    append_message(
        state,
        "assistant",
        f"Escena creada (modo={res.get('mode')}). Narrativa inicial lista. Puedes continuar con /narrar para seguir la historia.",
    )
    state["last_mode"] = "monitor"
    return state
