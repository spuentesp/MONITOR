"""State management for LangGraph modes."""
from __future__ import annotations

import uuid
from typing import Literal, NotRequired, TypedDict

from core.generation.interfaces.llm import Message

Mode = Literal["narration", "monitor"]


class GraphState(TypedDict, total=False):
    # Conversación acumulada
    messages: list[Message]
    # Último input del usuario (para el step actual)
    input: str
    # Modo actual decidido por el router
    mode: Mode
    # Modo del turno anterior (para continuidad)
    last_mode: NotRequired[Mode]
    # Override explícito para este turno (si existe)
    override_mode: NotRequired[Mode]
    # Contexto
    session_id: NotRequired[str]
    universe_id: NotRequired[str]
    user: NotRequired[dict]
    # Metadatos (confianza/razón del router, flags)
    meta: NotRequired[dict]


def append_message(state: GraphState, role: str, content: str) -> None:
    """Append a message to the state's message list."""
    msgs = state.get("messages") or []
    msgs.append({"role": role, "content": content})
    state["messages"] = msgs


def generate_id(prefix: str) -> str:
    """Generate a unique ID with the given prefix."""
    return f"{prefix}:{uuid.uuid4().hex[:8]}"
