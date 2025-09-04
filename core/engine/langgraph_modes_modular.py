"""Simplified LangGraph modes implementation using modular components."""

from __future__ import annotations

import re
from typing import Any, NotRequired, TypedDict
import uuid

from core.engine.tools import ToolContext
from core.generation.interfaces.llm import Message

from .modes.monitor import monitor_node as modular_monitor_node
from .modes.narration_mode import narration_node as modular_narration_node
from .modes.router import classify_intent as modular_classify_intent

# Import modular components
from .modes.state import GraphState as ModularGraphState
from .modes.state import Mode


# Legacy GraphState for backward compatibility
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


_CMD_MONITOR = re.compile(r"^[\s]*[\/@]?(monitor)\b", re.IGNORECASE)
_CMD_NARRATE = re.compile(r"^[\s]*[\/@]?(narrar|narrador|narrate|narrator)\b", re.IGNORECASE)
_CMD_HELP = re.compile(r"^[\s]*[\/@]?help\b", re.IGNORECASE)


def _append(state: GraphState, role: str, content: str) -> None:
    msgs = state.get("messages") or []
    msgs.append({"role": role, "content": content})
    state["messages"] = msgs


def _gen_id(prefix: str) -> str:
    return f"{prefix}:{uuid.uuid4().hex[:8]}"


def _convert_to_modular_state(state: GraphState) -> ModularGraphState:
    """Convert legacy GraphState to modular GraphState."""
    return {
        "messages": state.get("messages", []),
        "text": state.get("input", ""),
        "mode": state.get("mode"),
        "last_mode": state.get("last_mode"),
        "override_mode": state.get("override_mode"),
        "universe_id": state.get("universe_id"),
        "session_id": state.get("session_id"),
        "meta": state.get("meta", {}),
    }


def _convert_from_modular_state(modular_state: ModularGraphState) -> GraphState:
    """Convert modular GraphState back to legacy GraphState."""
    return {
        "messages": modular_state.get("messages", []),
        "input": modular_state.get("text", ""),
        "mode": modular_state.get("mode"),
        "last_mode": modular_state.get("last_mode"),
        "override_mode": modular_state.get("override_mode"),
        "universe_id": modular_state.get("universe_id"),
        "session_id": modular_state.get("session_id"),
        "meta": modular_state.get("meta", {}),
    }


def classify_intent(state: GraphState) -> GraphState:
    """Legacy wrapper for modular classify_intent."""
    modular_state = _convert_to_modular_state(state)
    result = modular_classify_intent(modular_state)
    return _convert_from_modular_state(result)


def narration_node(state: GraphState, ctx: ToolContext | None = None) -> GraphState:
    """Legacy wrapper for modular narration_node."""
    modular_state = _convert_to_modular_state(state)
    result = modular_narration_node(modular_state, ctx)
    return _convert_from_modular_state(result)


def monitor_node(state: GraphState, ctx: ToolContext | None = None) -> GraphState:
    """Legacy wrapper for modular monitor_node."""
    modular_state = _convert_to_modular_state(state)
    result = modular_monitor_node(modular_state, ctx)
    return _convert_from_modular_state(result)


def build_langgraph_modes(tools: ToolContext | None = None) -> Any:
    """Compila un grafo de un solo paso que enruta Narrador vs Monitor.

    Mantiene la importación de langgraph perezosa para no forzar dependencia en import-time.
    Devuelve un objeto con .invoke(state_dict) -> state_dict.
    """
    try:
        from langgraph.graph import END, StateGraph
    except Exception:  # pragma: no cover - entorno sin langgraph
        # Fallback sin langgraph: adaptador que ejecuta secuencialmente
        class _SeqAdapter:
            def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
                s = dict(state)
                s = classify_intent(s)
                if s.get("mode", "narration") == "narration":
                    return narration_node(s, tools)
                else:
                    return monitor_node(s, tools)

        return _SeqAdapter()

    def should_continue(state: GraphState) -> str:
        return state.get("mode", "narration")

    # Build the graph
    workflow = StateGraph(GraphState)
    workflow.add_node("classify_intent", lambda s: classify_intent(s))
    workflow.add_node("narration", lambda s: narration_node(s, tools))
    workflow.add_node("monitor", lambda s: monitor_node(s, tools))

    # Set entry point and edges
    workflow.set_entry_point("classify_intent")
    workflow.add_conditional_edges(
        "classify_intent",
        should_continue,
        {"narration": "narration", "monitor": "monitor"},
    )
    workflow.add_edge("narration", END)
    workflow.add_edge("monitor", END)

    return workflow.compile()
