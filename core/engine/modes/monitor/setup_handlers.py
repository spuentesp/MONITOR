"""Story and universe setup handlers for monitor mode."""

from __future__ import annotations

from core.agents.narrator import narrator_agent
from core.engine.monitor_parser import MonitorIntent
from core.generation.providers import select_llm_from_env

from ..state import GraphState, append_message, generate_id
from .utils import (
    clear_wizard_state,
    commit_deltas,
    get_wizard_state,
    update_wizard_state,
)


def handle_start_story(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle the start_story action to create a complete story scaffolding."""
    # Gather topics/interests and optional names
    w = dict(get_wizard_state(state))
    w.update({"flow": "gm_onboarding"})
    if intent.topics:
        w["topics"] = intent.topics
    if intent.interests:
        w["interests"] = intent.interests
    if intent.system_id:
        w["system_id"] = intent.system_id
    if intent.name:
        w["universe_name"] = intent.name
    if intent.description:
        w["story_title"] = intent.description
    update_wizard_state(state, w)

    # Ask for missing bits
    missing = []
    if not w.get("topics"):
        missing.append('topics (e.g., topics "superheroes, urban mystery")')
    if not w.get("story_title"):
        missing.append('story title (e.g., story "Night Shift")')
    if missing:
        append_message(
            state,
            "assistant",
            "To start your story, please provide: " + ", ".join(missing) + ".",
        )
        state["last_mode"] = "monitor"
        return state

    # Create scaffolding: multiverse, universe, arc, story, initial scene
    mv_id = state.get("multiverse_id") or generate_id("multiverse")
    uni_id = state.get("universe_id") or generate_id("universe")
    arc_id = generate_id("arc")
    st_id = generate_id("story")
    sc_id = generate_id("scene")

    # Prepare deltas
    deltas = {
        "new_multiverse": {"id": mv_id, "name": (w.get("universe_name") or "GM Session")},
        "new_universe": {
            "id": uni_id,
            "name": (w.get("universe_name") or "GM Session"),
            "multiverse_id": mv_id,
        },
        "new_arc": {"id": arc_id, "title": "Session Arc", "universe_id": uni_id},
        "new_story": {
            "id": st_id,
            "title": w.get("story_title"),
            "universe_id": uni_id,
            "arc_id": arc_id,
            "sequence_index": 1,
        },
        "new_scene": {
            "id": sc_id,
            "title": "Scene 1",
            "story_id": st_id,
            "participants": [],
        },
        "universe_id": uni_id,
        "_draft": f"Start GM story: {w.get('story_title')}",
    }
    res = commit_deltas(ctx, deltas)

    # Generate an intro beat and persist as Fact
    try:
        llm = select_llm_from_env()
        agent = narrator_agent(llm)
        topics_text = ", ".join(w.get("topics") or [])
        primer = agent.act(
            [
                {
                    "role": "system",
                    "content": "You are the GM. Write a short intro beat (3-5 sentences) based on the given topics and interests. Keep it engaging and concise.",
                },
                {
                    "role": "user",
                    "content": f"Topics: {topics_text}. Interests: {', '.join(w.get('interests') or [])}.",
                },
            ]
        )
        commit_deltas(
            ctx,
            {
                "facts": [{"description": primer, "occurs_in": sc_id, "universe_id": uni_id}],
                "_draft": primer[:120],
            },
        )
    except Exception:
        pass

    # Save session context and inform user
    state["multiverse_id"] = mv_id
    state["universe_id"] = uni_id
    state["story_id"] = st_id
    state["scene_id"] = sc_id

    # Clear wizard to avoid loops
    clear_wizard_state(state)

    append_message(
        state,
        "assistant",
        f"Story created (mode={res.get('mode')}). You can now /narrate to continue from the intro.",
    )
    state["last_mode"] = "monitor"
    return state


def handle_setup_universe(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle the setup_universe action for step-by-step universe creation."""
    # Estado del wizard en meta.wizard
    w = dict(get_wizard_state(state))
    w.setdefault("flow", "setup_universe")
    if intent.id:
        w["universe_id"] = intent.id
    if intent.name:
        w["name"] = intent.name
    if intent.multiverse_id:
        w["multiverse_id"] = intent.multiverse_id

    # Paso a paso: pedir faltantes
    missing = []
    if not w.get("multiverse_id") and not state.get("multiverse_id"):
        missing.append("multiverse_id (p.ej. multiverse mv:demo)")
    if not w.get("name"):
        missing.append('name (p.ej. nombre "Mi Universo")')

    # Si faltan datos, pedirlos
    if missing:
        update_wizard_state(state, w)
        append_message(
            state,
            "assistant",
            "Configurar universo: por favor indica " + ", ".join(missing) + ".",
        )
        state["last_mode"] = "monitor"
        return state

    # Tenemos suficientes datos → crear universo
    mv_id = w.get("multiverse_id") or state.get("multiverse_id")
    uid = w.get("universe_id") or generate_id("universe")
    new_u = {"id": uid, "name": w.get("name"), "multiverse_id": mv_id}
    res = commit_deltas(
        ctx, {"new_universe": new_u, "universe_id": uid, "_draft": f"Setup universo {uid}"}
    )

    # Continuar wizard: crear historia
    update_wizard_state(state, {"flow": "setup_story", "universe_id": uid})
    state["universe_id"] = uid
    append_message(
        state,
        "assistant",
        f'Universo configurado (modo={res.get("mode")}). Indica el nombre de la historia inicial (p.ej. nombre "Prólogo").',
    )
    state["last_mode"] = "monitor"
    return state
