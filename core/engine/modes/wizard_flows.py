"""Multi-turn setup wizards for story creation."""

from __future__ import annotations

from core.agents.narrator import narrator_agent
from core.generation.providers import select_llm_from_env

from .graph_state import GraphState, append_message, generate_id


def handle_start_story_wizard(state: GraphState, intent: Any) -> GraphState:
    """Handle the start_story wizard flow."""
    # Gather topics/interests and optional names
    meta = state.get("meta") or {}
    w = dict(meta.get("wizard") or {})
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

    meta["wizard"] = w
    state["meta"] = meta

    # Check for missing information
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

    # Create the story structure
    return _create_story_structure(state, w)


def handle_setup_universe_wizard(state: GraphState, intent: Any) -> GraphState:
    """Handle the setup_universe wizard flow."""
    wizard = (state.get("meta") or {}).get("wizard") or {}
    w = dict(wizard)
    w.setdefault("flow", "setup_universe")

    if intent.id:
        w["universe_id"] = intent.id
    if intent.name:
        w["name"] = intent.name
    if intent.multiverse_id:
        w["multiverse_id"] = intent.multiverse_id

    # Check for missing data
    missing = []
    if not w.get("multiverse_id") and not state.get("multiverse_id"):
        missing.append("multiverse_id (p.ej. multiverse mv:demo)")
    if not w.get("name"):
        missing.append('name (p.ej. nombre "Mi Universo")')

    if missing:
        meta = state.get("meta") or {}
        meta["wizard"] = w
        state["meta"] = meta
        append_message(
            state,
            "assistant",
            "Configurar universo: por favor indica " + ", ".join(missing) + ".",
        )
        state["last_mode"] = "monitor"
        return state

    # Create the universe
    return _create_universe(state, w)


def _create_story_structure(state: GraphState, wizard_data: dict) -> GraphState:
    """Create the complete story scaffolding."""
    from .monitor_actions import commit_deltas

    # Generate IDs
    mv_id = state.get("multiverse_id") or generate_id("multiverse")
    uni_id = state.get("universe_id") or generate_id("universe")
    arc_id = generate_id("arc")
    st_id = generate_id("story")
    sc_id = generate_id("scene")

    # Prepare creation deltas
    deltas = {
        "new_multiverse": {"id": mv_id, "name": (wizard_data.get("universe_name") or "GM Session")},
        "new_universe": {
            "id": uni_id,
            "name": (wizard_data.get("universe_name") or "GM Session"),
            "multiverse_id": mv_id,
        },
        "new_arc": {"id": arc_id, "title": "Session Arc", "universe_id": uni_id},
        "new_story": {
            "id": st_id,
            "title": wizard_data.get("story_title"),
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
        "_draft": f"Start GM story: {wizard_data.get('story_title')}",
    }

    res = commit_deltas(state, deltas)

    # Generate intro beat
    _generate_intro_beat(state, wizard_data, sc_id, uni_id)

    # Update state with new IDs
    state["multiverse_id"] = mv_id
    state["universe_id"] = uni_id
    state["story_id"] = st_id
    state["scene_id"] = sc_id

    # Clear wizard
    meta = state.get("meta") or {}
    meta.pop("wizard", None)
    state["meta"] = meta

    append_message(
        state,
        "assistant",
        f"Story created (mode={res.get('mode')}). You can now /narrate to continue from the intro.",
    )
    state["last_mode"] = "monitor"
    return state


def _create_universe(state: GraphState, wizard_data: dict) -> GraphState:
    """Create a new universe and set up story wizard."""
    from .monitor_actions import commit_deltas

    mv_id = wizard_data.get("multiverse_id") or state.get("multiverse_id")
    uid = wizard_data.get("universe_id") or generate_id("universe")

    new_u = {"id": uid, "name": wizard_data.get("name"), "multiverse_id": mv_id}
    res = commit_deltas(
        state, {"new_universe": new_u, "universe_id": uid, "_draft": f"Setup universo {uid}"}
    )

    # Continue wizard: create story
    meta = state.get("meta") or {}
    meta["wizard"] = {"flow": "setup_story", "universe_id": uid}
    state["meta"] = meta
    state["universe_id"] = uid

    append_message(
        state,
        "assistant",
        f'Universo configurado (modo={res.get("mode")}). Indica el nombre de la historia inicial (p.ej. nombre "Prólogo").',
    )
    state["last_mode"] = "monitor"
    return state


def _generate_intro_beat(
    state: GraphState, wizard_data: dict, scene_id: str, universe_id: str
) -> None:
    """Generate and persist an intro beat for the story."""
    try:
        from .monitor_actions import commit_deltas

        llm = select_llm_from_env()
        agent = narrator_agent(llm)
        topics_text = ", ".join(wizard_data.get("topics") or [])

        primer = agent.act(
            [
                {
                    "role": "system",
                    "content": "You are the GM. Write a short intro beat (3-5 sentences) based on the given topics and interests. Keep it engaging and concise.",
                },
                {
                    "role": "user",
                    "content": f"Topics: {topics_text}. Interests: {', '.join(wizard_data.get('interests') or [])}.",
                },
            ]
        )

        commit_deltas(
            state,
            {
                "facts": [
                    {"description": primer, "occurs_in": scene_id, "universe_id": universe_id}
                ],
                "_draft": primer[:120],
            },
        )
    except Exception:
        pass
