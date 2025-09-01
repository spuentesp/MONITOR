from __future__ import annotations

import json
import re
from typing import Any, Literal, NotRequired, TypedDict

from core.agents.narrator import narrator_agent
from core.engine.tools import ToolContext, query_tool, recorder_tool
from core.engine.monitor_parser import parse_monitor_intent
from core.generation.interfaces.llm import Message
from core.generation.providers import select_llm_from_env


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


_CMD_MONITOR = re.compile(r"^[\s]*[\/@]?(monitor)\b", re.IGNORECASE)
_CMD_NARRATE = re.compile(r"^[\s]*[\/@]?(narrar|narrador|narrate|narrator)\b", re.IGNORECASE)
_CMD_HELP = re.compile(r"^[\s]*[\/@]?help\b", re.IGNORECASE)


def _append(state: GraphState, role: str, content: str) -> None:
    msgs = state.get("messages") or []
    msgs.append({"role": role, "content": content})
    state["messages"] = msgs


def get_help_text() -> str:
    return (
        "Comandos disponibles (prefijo opcional / o @):\n"
        "- /help: muestra este mensaje de ayuda.\n"
        "- /monitor <pedido>: fuerza modo Monitor para administración (crear/actualizar/consultar).\n"
        "- /narrar <mensaje>: fuerza modo Narración para continuar la historia.\n"
        "Consejo: si mezclas narrativa y administración, el enrutador intentará decidir, pero puedes forzar el modo con los comandos."
    )


def classify_intent(state: GraphState) -> GraphState:
    """Router: decide Narración vs Monitor usando heurística + LLM opcional.

    Honra override_mode si está presente en el estado.
    """
    text = state.get("input") or ""
    last_mode: Mode = state.get("last_mode", "narration")  # default narrativo
    mode: Mode = last_mode
    reason = "fallback"
    confidence = 0.55

    # Overrides explícitos
    override = state.get("override_mode")
    if override in ("narration", "monitor"):
        state["mode"] = override  # decide ya
        meta = state.get("meta") or {}
        meta.update({"router": {"confidence": 1.0, "reason": f"override:{override}", "decided": override}})
        state["meta"] = meta
        return state

    # Heurísticas rápidas
    t = text.strip()
    if _CMD_HELP.match(t):
        # Help se maneja como monitor para presentar ayuda
        mode, reason, confidence = "monitor", "help", 0.99
        state["_help"] = True  # flag interna
    elif _CMD_MONITOR.match(t):
        mode, reason, confidence = "monitor", "command_prefix", 0.95
    elif _CMD_NARRATE.match(t):
        mode, reason, confidence = "narration", "command_prefix", 0.95
    elif any(k in t.lower() for k in [
        "monitor:", "administra", "configura", "crea", "actualiza", "consulta", "borra",
        "persistir", "guardar", "dataset", "índice", "indice", "vector", "embedding",
    ]):
        mode, reason, confidence = "monitor", "keywords", 0.75
    elif any(k in t.lower() for k in [
        "cuenta", "narra", "qué pasó", "que paso", "continúa", "continua", "siguiente capítulo",
        "siguiente capitulo", "rol", "personaje",
    ]):
        mode, reason, confidence = "narration", "keywords", 0.7

    # Clasificador LLM (refina decisión) – robusto a backend mock
    try:
        llm = select_llm_from_env()
        sys = (
            "Clasifica el mensaje como 'narration' (historia diegética) o 'monitor' "
            "(operaciones del sistema: crear/actualizar/consultar, admin, ERPs, APIs). "
            "Responde SOLO JSON: {\"intent\":\"narration|monitor\",\"confidence\":0.0-1.0,\"reason\":\"...\"}."
        )
        user = f"Mensaje: {text}\nÚltimo modo: {last_mode}"
        out = llm.complete(system_prompt=sys, messages=[{"role": "user", "content": user}], temperature=0.0, max_tokens=120)
        data = json.loads(out) if isinstance(out, str) else {}
        lm_intent = str(data.get("intent", "")).lower()
        lm_conf = float(data.get("confidence", 0.0))
        lm_reason = str(data.get("reason", ""))
        if lm_intent in ("narration", "monitor") and (lm_conf >= confidence or reason == "fallback"):
            mode, confidence, reason = lm_intent, lm_conf, f"llm:{lm_reason}"
    except Exception:
        pass

    state["mode"] = mode
    meta = state.get("meta") or {}
    meta.update({"router": {"confidence": confidence, "reason": reason, "decided": mode}})
    state["meta"] = meta
    return state


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
    _append(state, "assistant", reply)
    state["last_mode"] = "narration"
    return state


def monitor_node(state: GraphState) -> GraphState:
    """Responde como Monitor (operacional). MVP: texto accionable; help si se solicita.

    En futuras iteraciones, este nodo debería orquestar acciones reales (Query/Recorder).
    """
    text = state.get("input", "").strip()
    if state.get("_help") or _CMD_HELP.match(text):
        reply = get_help_text()
        _append(state, "assistant", reply)
        state["last_mode"] = "monitor"
        return state

    # Intentos de acción reales vía ToolContext + parser
    ctx: ToolContext | None = state.get("tools")  # type: ignore[assignment]
    universe_id = state.get("universe_id")
    action_reply: str | None = None

    def _commit(deltas: dict) -> dict:
        if not ctx:
            return {"mode": "noop", "reason": "no_tool_context"}
        draft = deltas.get("_draft", "")
        return recorder_tool(ctx, draft=draft, deltas={k: v for k, v in deltas.items() if k != "_draft"})

    intent = parse_monitor_intent(text)
    if intent:
        if intent.action == "create_multiverse":
            new_mv = {"id": intent.id, "name": intent.name, "omniverse_id": state.get("omniverse_id")}
            res = _commit({"new_multiverse": new_mv, "_draft": f"Crear multiverso {intent.id or '(auto-id)'}"})
            action_reply = f"Multiverso creado (modo={res.get('mode')})."
        elif intent.action == "create_universe":
            mv_id = intent.multiverse_id or state.get("multiverse_id")
            new_u = {"id": intent.id, "name": intent.name, "multiverse_id": mv_id, "description": None}
            res = _commit({"new_universe": new_u, "universe_id": universe_id, "_draft": f"Crear universo {intent.id or '(auto-id)'}"})
            action_reply = f"Universo creado (modo={res.get('mode')})."
        elif intent.action == "save_fact":
            desc = (intent.description or "").strip()
            fact = {"description": desc or "(sin descripción)", "universe_id": universe_id}
            if intent.scene_id or state.get("scene_id"):
                fact["occurs_in"] = intent.scene_id or state.get("scene_id")
            res = _commit({"facts": [fact], "universe_id": universe_id, "_draft": desc[:120]})
            action_reply = f"Hecho guardado (modo={res.get('mode')})."

    if action_reply is None:
        # Respuesta LLM por defecto (consejos/plan)
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

    _append(state, "assistant", reply)
    state["last_mode"] = "monitor"
    return state


def build_langgraph_modes(tools: ToolContext | None = None) -> Any:
    """Compila un grafo de un solo paso que enruta Narrador vs Monitor.

    Mantiene la importación de langgraph perezosa para no forzar dependencia en import-time.
    Devuelve un objeto con .invoke(state_dict) -> state_dict.
    """
    try:
        from langgraph.graph import END, StateGraph
    except Exception as e:  # pragma: no cover - entorno sin langgraph
        # Fallback sin langgraph: adaptador que ejecuta secuencialmente
        class _SeqAdapter:
            def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
                s = dict(state)
                s = classify_intent(s)
                if s.get("mode", "narration") == "narration":
                    s = narrator_node(s)
                else:
                    s = monitor_node(s)
                return s

        return _SeqAdapter()

    class S(dict):
        pass

    g = StateGraph(S)
    g.add_node("classify", classify_intent)
    g.add_node("narrator", narrator_node)
    g.add_node("monitor", monitor_node)
    g.set_entry_point("classify")

    def pick_branch(state: GraphState) -> str:
        mode = state.get("mode", "narration")
        return "narrator" if mode == "narration" else "monitor"

    g.add_conditional_edges("classify", pick_branch, {"narrator": "narrator", "monitor": "monitor"})
    g.add_edge("narrator", END)
    g.add_edge("monitor", END)

    compiled = g.compile()

    class _Adapter:
        def __init__(self, _compiled):
            self._compiled = _compiled

        def invoke(self, inputs: dict[str, Any]) -> dict[str, Any]:
            try:
                # Propaga ToolContext al estado
                if tools is not None:
                    inputs = dict(inputs)
                    inputs["tools"] = tools  # type: ignore[index]
                out = self._compiled.invoke(inputs)
                if out is not None:
                    return out
            except Exception:
                pass
            # Fallback secuencial para robustez
            s = dict(inputs)
            if tools is not None:
                s["tools"] = tools  # type: ignore[index]
            s = classify_intent(s)
            if s.get("mode", "narration") == "narration":
                s = narrator_node(s)
            else:
                s = monitor_node(s)
            return s

    return _Adapter(compiled)
