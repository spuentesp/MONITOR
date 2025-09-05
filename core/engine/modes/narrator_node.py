"""Narrator node for creative storytelling responses."""

from __future__ import annotations

from core.agents.narrator import narrator_agent
from core.generation.interfaces.llm import Message
from core.generation.providers import select_llm_from_env

from .graph_state import GraphState, append_message


def narrator_node(state: GraphState) -> GraphState:
    """Respond as Narrator (creative/diegetic mode)."""
    llm = select_llm_from_env()
    agent = narrator_agent(llm)
    universe = state.get("universe_id") or "default"

    # Add context as system message
    system_context = f"Universo actual: {universe}. Mantén tono diegético, conciso."
    msgs: list[Message] = list(state.get("messages") or [])

    if system_context:
        msgs.append({"role": "system", "content": system_context})

    msgs.append({"role": "user", "content": state.get("input", "")})

    # Generate response using last 8 messages for context
    reply = agent.act(msgs[-8:])

    append_message(state, "assistant", reply)
    state["last_mode"] = "narration"

    return state
