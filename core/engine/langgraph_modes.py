from __future__ import annotations

import json
import re
from typing import Any, Literal, NotRequired, TypedDict
import uuid

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


def _gen_id(prefix: str) -> str:
    return f"{prefix}:{uuid.uuid4().hex[:8]}"


def get_help_text() -> str:
    return (
        "Comandos disponibles (prefijo opcional / o @):\n"
        "- /help: muestra este mensaje de ayuda.\n"
        "- /monitor <pedido>: fuerza modo Monitor para administración (crear/actualizar/consultar).\n"
        "- /narrar <mensaje>: fuerza modo Narración para continuar la historia.\n"
    "- /monitor iniciar universo [<id>] [nombre \"...\"] [multiverso <id>]: asistente para crear un universo listo para narrar.\n"
    "Consultas útiles (EN): list multiverses | list universes [multiverse <id>] | list stories [universe <id>] | show 'Tony Stark' in universe <id> | enemies of 'Rogue' in universe <id> | last time they saw 'Deadpool' in universe <id>.\n"
    "Consejo: si mezclas narrativa y administración, el enrutador intentará decidir, pero puedes forzar el modo con los comandos.\n"
    "Persistencia: este endpoint opera en 'copilot' (dry-run/staging) por defecto. Envía mode='autopilot' para persistir en Neo4j."
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

    # Wizard de setup de universo (multi-turn)
    wizard = (state.get("meta") or {}).get("wizard") or {}
    intent = parse_monitor_intent(text)
    if intent:
        if intent.action == "setup_universe":
            # Estado del wizard en meta.wizard
            w = dict(wizard)
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
                meta = state.get("meta") or {}
                meta["wizard"] = w
                state["meta"] = meta
                _append(state, "assistant", "Configurar universo: por favor indica " + ", ".join(missing) + ".")
                state["last_mode"] = "monitor"
                return state
            # Tenemos suficientes datos → crear universo
            mv_id = w.get("multiverse_id") or state.get("multiverse_id")
            uid = w.get("universe_id") or _gen_id("universe")
            new_u = {"id": uid, "name": w.get("name"), "multiverse_id": mv_id}
            res = _commit({"new_universe": new_u, "universe_id": uid, "_draft": f"Setup universo {uid}"})
            # Continuar wizard: crear historia
            meta = state.get("meta") or {}
            meta["wizard"] = {"flow": "setup_story", "universe_id": uid}
            state["meta"] = meta
            state["universe_id"] = uid
            _append(state, "assistant", f"Universo configurado (modo={res.get('mode')}). Indica el nombre de la historia inicial (p.ej. nombre \"Prólogo\").")
            state["last_mode"] = "monitor"
            return state
        
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
        elif intent.action == "list_multiverses":
            try:
                rows = query_tool(ctx, "list_multiverses") if ctx else []
                if not rows:
                    action_reply = "No multiverses found."
                else:
                    lines = [f"- {r.get('name') or r.get('id')} ({r.get('id')})" for r in rows]
                    action_reply = "Multiverses:\n" + "\n".join(lines)
            except Exception as e:
                action_reply = f"Error listing multiverses: {e}"
        elif intent.action == "list_universes":
            mv = intent.multiverse_id or state.get("multiverse_id")
            if not mv:
                action_reply = "Please specify a multiverse id (e.g., multiverse mv:demo)."
            else:
                try:
                    rows = query_tool(ctx, "list_universes_for_multiverse", multiverse_id=mv) if ctx else []
                    if not rows:
                        action_reply = f"No universes found in {mv}."
                    else:
                        lines = [f"- {r.get('name') or r.get('id')} ({r.get('id')})" for r in rows]
                        action_reply = f"Universes in {mv}:\n" + "\n".join(lines)
                except Exception as e:
                    action_reply = f"Error listing universes: {e}"
        elif intent.action == "list_stories":
            uid = intent.universe_id or state.get("universe_id")
            if not uid:
                action_reply = "Please specify a universe id (e.g., universe u:demo)."
            else:
                try:
                    rows = query_tool(ctx, "stories_in_universe", universe_id=uid) if ctx else []
                    if not rows:
                        action_reply = f"No stories found in {uid}."
                    else:
                        lines = [
                            f"- {r.get('title') or r.get('id')} (id={r.get('id')}, arc={r.get('arc_id') or '-'}, seq={r.get('sequence_index')})"
                            for r in rows
                        ]
                        action_reply = f"Stories in {uid}:\n" + "\n".join(lines)
                except Exception as e:
                    action_reply = f"Error listing stories: {e}"
        elif intent.action == "show_entity_info":
            uid = intent.universe_id or state.get("universe_id")
            name = (intent.entity_name or "").strip()
            if not uid or not name:
                action_reply = "Please provide an entity name and universe (e.g., show 'Tony Stark' in universe u:demo)."
            else:
                try:
                    ent = query_tool(ctx, "entity_by_name_in_universe", universe_id=uid, name=name) if ctx else None
                    if not ent:
                        action_reply = f"Entity '{name}' not found in {uid}."
                    else:
                        # basic appearances and facts
                        scenes = query_tool(ctx, "scenes_for_entity", entity_id=ent["id"]) if ctx else []
                        info = [f"Entity: {ent['name']} (id={ent['id']}, type={ent.get('type') or '-'})"]
                        if scenes:
                            info.append("Appears in scenes:")
                            info.extend([f"  - story={s.get('story_id')}, scene={s.get('scene_id')}, seq={s.get('sequence_index')}" for s in scenes])
                        action_reply = "\n".join(info)
                except Exception as e:
                    action_reply = f"Error fetching entity info: {e}"
        elif intent.action == "list_enemies":
            uid = intent.universe_id or state.get("universe_id")
            name = (intent.entity_name or "").strip()
            if not uid or not name:
                action_reply = "Please provide a character name and universe (e.g., enemies of 'Rogue' in universe u:demo)."
            else:
                try:
                    ent = query_tool(ctx, "entity_by_name_in_universe", universe_id=uid, name=name) if ctx else None
                    if not ent:
                        action_reply = f"Entity '{name}' not found in {uid}."
                    else:
                        # MVP heuristic: list entities with role='ENEMY' in universe
                        rows = query_tool(ctx, "entities_in_universe_by_role", universe_id=uid, role="ENEMY") if ctx else []
                        lines = [f"- {r.get('name')} ({r.get('id')})" for r in rows] if rows else []
                        action_reply = (f"Enemies in {uid}:\n" + "\n".join(lines)) if lines else f"No enemies found in {uid}."
                except Exception as e:
                    action_reply = f"Error listing enemies: {e}"
        elif intent.action == "last_seen":
            uid = intent.universe_id or state.get("universe_id")
            name = (intent.entity_name or "").strip()
            if not uid or not name:
                action_reply = "Please provide a character name and universe (e.g., last time they saw 'Deadpool' in universe u:demo)."
            else:
                try:
                    ent = query_tool(ctx, "entity_by_name_in_universe", universe_id=uid, name=name) if ctx else None
                    if not ent:
                        action_reply = f"Entity '{name}' not found in {uid}."
                    else:
                        # Find scenes for entity then pick the highest sequence index per story
                        scenes = query_tool(ctx, "scenes_for_entity", entity_id=ent["id"]) if ctx else []
                        if not scenes:
                            action_reply = f"No appearances found for {name}."
                        else:
                            # Simple sort by (story_id, sequence_index)
                            scenes_sorted = sorted(scenes, key=lambda s: (s.get("story_id"), s.get("sequence_index") or -1))
                            last = scenes_sorted[-1]
                            action_reply = (
                                f"Last seen in story={last.get('story_id')}, scene={last.get('scene_id')} (seq={last.get('sequence_index')})."
                            )
                except Exception as e:
                    action_reply = f"Error computing last seen: {e}"

        # Avanzar wizard si está activo y no hubo intent directo que lo cierre
        wizard = (state.get("meta") or {}).get("wizard") or {}
        if wizard:
            flow = wizard.get("flow")
            if flow == "setup_story":
                m = re.search(r"(?:nombre|name)\s+\"([^\"]+)\"|'([^']+)'", text, flags=re.IGNORECASE)
                title = (m.group(1) or m.group(2)) if m else None
                if not title:
                    _append(state, "assistant", "Por favor indica el nombre de la historia (p.ej. nombre \"Prólogo\").")
                    state["last_mode"] = "monitor"
                    return state
                st_id = _gen_id("story")
                u_id = wizard.get("universe_id") or state.get("universe_id")
                new_story = {"id": st_id, "title": title, "universe_id": u_id}
                res = _commit({"new_story": new_story, "universe_id": u_id, "_draft": f"Crear historia {title}"})
                # Paso a escena
                meta = state.get("meta") or {}
                meta["wizard"] = {"flow": "setup_scene", "universe_id": u_id, "story_id": st_id}
                state["meta"] = meta
                _append(state, "assistant", f"Historia creada (modo={res.get('mode')}). Indica el nombre de la escena inicial (p.ej. nombre \"Escena 1: Llegada\").")
                state["last_mode"] = "monitor"
                return state
            if flow == "setup_scene":
                m = re.search(r"(?:nombre|name)\s+\"([^\"]+)\"|'([^']+)'", text, flags=re.IGNORECASE)
                title = (m.group(1) or m.group(2)) if m else None
                if not title:
                    _append(state, "assistant", "Por favor indica el nombre de la escena (p.ej. nombre \"Escena 1\").")
                    state["last_mode"] = "monitor"
                    return state
                sc_id = _gen_id("scene")
                story_id = wizard.get("story_id")
                new_scene = {"id": sc_id, "title": title, "story_id": story_id}
                res = _commit({"new_scene": new_scene, "_draft": f"Crear escena {title}"})
                state["scene_id"] = sc_id
                # Generar narrativa inicial y guardarla como fact
                try:
                    llm = select_llm_from_env()
                    agent = narrator_agent(llm)
                    primer = agent.act([
                        {"role": "system", "content": "Genera un inicio breve (3-5 frases) para la primera escena dada su premisa/título."},
                        {"role": "user", "content": f"Escena: {title}. Presenta un gancho inmersivo."},
                    ])
                    _commit({"facts": [{"description": primer, "occurs_in": sc_id}], "_draft": primer[:120]})
                except Exception:
                    pass
                # Cerrar wizard
                meta = state.get("meta") or {}
                meta.pop("wizard", None)
                state["meta"] = meta
                _append(state, "assistant", f"Escena creada (modo={res.get('mode')}). Narrativa inicial lista. Puedes continuar con /narrar para seguir la historia.")
                state["last_mode"] = "monitor"
                return state

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
