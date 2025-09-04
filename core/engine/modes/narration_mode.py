"""Narration mode implementation."""
from __future__ import annotations

from core.agents.narrator import narrator_agent
from core.generation.interfaces.llm import Message
from core.generation.providers import select_llm_from_env
from .state import GraphState, append_message


def narrator_node(state: GraphState) -> GraphState:
    """Responde como Narrador (diegético)."""
    llm = select_llm_from_env()
    agent = narrator_agent(llm)
    universe = state.get("universe_id") or "default"
    # Contexto breve como system si se quiere enriquecer en siguientes iteraciones
    system_context = f"Universo actual: {universe}. Mantén tono diegético, conciso."
    msgs: list[Message] = list(state.get("messages") or [])
    if system_context:
        msgs.append({"role": "system", "content": system_context})
    msgs.append({"role": "user", "content": state.get("input", "")})
    reply = agent.act(msgs[-8:])
    append_message(state, "assistant", reply)
    state["last_mode"] = "narration"
    return state
