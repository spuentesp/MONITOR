"""Graph state management and utilities for LangGraph modes.

This module contains the state definition and helper functions
for managing conversation state across nodes.
"""
from __future__ import annotations

import uuid
from typing import Any, Literal, NotRequired, TypedDict

from core.generation.interfaces.llm import Message

Mode = Literal["narration", "monitor"]


class GraphState(TypedDict, total=False):
    """State shared across all graph nodes."""
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
    multiverse_id: NotRequired[str]
    omniverse_id: NotRequired[str]
    story_id: NotRequired[str]
    scene_id: NotRequired[str]
    user: NotRequired[dict]
    # Metadatos (confianza/razón del router, flags)
    meta: NotRequired[dict]
    # Tools context
    tools: NotRequired[Any]
    # Internal flags
    _help: NotRequired[bool]


def append_message(state: GraphState, role: str, content: str) -> None:
    """Add a message to the conversation history."""
    msgs = state.get("messages") or []
    msgs.append({"role": role, "content": content})
    state["messages"] = msgs


def generate_id(prefix: str) -> str:
    """Generate a unique ID with the given prefix."""
    return f"{prefix}:{uuid.uuid4().hex[:8]}"
