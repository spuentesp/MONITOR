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
from core.engine.attribute_extractor import distill_entity_attributes


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
    "GM onboarding: start a new story [topics \"urban fantasy, heists\"] [story \"Night Shift\"] | save conversation | end scene.\n"
    "Consejo: si mezclas narrativa y administración, el enrutador intentará decidir, pero puedes forzar el modo con los comandos.\n"
    "Persistencia: este endpoint opera en 'copilot' (dry-run/staging) por defecto. 'end scene' intenta persistir automáticamente los cambios en staging; envía mode='autopilot' para persistir siempre."
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

    def _auto_flush_if_needed(reason: str) -> dict | None:
        """If running in copilot (dry_run), flush staged changes at safe boundaries.

        This persists via the staging store regardless of ctx.dry_run, which is intentional for
        boundary commits like end_scene. In autopilot (dry_run=False), writes are already persisted.
        """
        try:
            if ctx and getattr(ctx, "dry_run", True):
                # Lazy import to avoid any circulars at module import time
                from core.engine.orchestrator import flush_staging

                return flush_staging(ctx)  # type: ignore[arg-type]
        except Exception:
            return {"ok": False, "error": "auto_flush_failed"}
        return None

    # Wizard de setup de universo (multi-turn)
    wizard = (state.get("meta") or {}).get("wizard") or {}
    intent = parse_monitor_intent(text)
    if intent:
        if intent.action == "start_story":
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
            # Ask for missing bits
            missing = []
            if not w.get("topics"):
                missing.append('topics (e.g., topics "superheroes, urban mystery")')
            if not w.get("story_title"):
                missing.append('story title (e.g., story "Night Shift")')
            if missing:
                _append(state, "assistant", "To start your story, please provide: " + ", ".join(missing) + ".")
                state["last_mode"] = "monitor"
                return state
            # Create scaffolding: multiverse, universe, arc, story, initial scene
            mv_id = state.get("multiverse_id") or _gen_id("multiverse")
            uni_id = state.get("universe_id") or _gen_id("universe")
            arc_id = _gen_id("arc")
            st_id = _gen_id("story")
            sc_id = _gen_id("scene")
            # Prepare deltas
            deltas = {
                "new_multiverse": {"id": mv_id, "name": (w.get("universe_name") or "GM Session")},
                "new_universe": {"id": uni_id, "name": (w.get("universe_name") or "GM Session"), "multiverse_id": mv_id},
                "new_arc": {"id": arc_id, "title": "Session Arc", "universe_id": uni_id},
                "new_story": {"id": st_id, "title": w.get("story_title"), "universe_id": uni_id, "arc_id": arc_id, "sequence_index": 1},
                "new_scene": {"id": sc_id, "title": "Scene 1", "story_id": st_id, "participants": []},
                "universe_id": uni_id,
                "_draft": f"Start GM story: {w.get('story_title')}",
            }
            res = _commit(deltas)
            # Generate an intro beat and persist as Fact
            try:
                llm = select_llm_from_env()
                agent = narrator_agent(llm)
                topics_text = ", ".join(w.get("topics") or [])
                primer = agent.act([
                    {"role": "system", "content": "You are the GM. Write a short intro beat (3-5 sentences) based on the given topics and interests. Keep it engaging and concise."},
                    {"role": "user", "content": f"Topics: {topics_text}. Interests: {', '.join(w.get('interests') or [])}."},
                ])
                _commit({"facts": [{"description": primer, "occurs_in": sc_id, "universe_id": uni_id}], "_draft": primer[:120]})
            except Exception:
                pass
            # Save session context and inform user
            state["multiverse_id"] = mv_id
            state["universe_id"] = uni_id
            state["story_id"] = st_id
            state["scene_id"] = sc_id
            # Clear wizard to avoid loops
            meta.pop("wizard", None)
            state["meta"] = meta
            _append(state, "assistant", f"Story created (mode={res.get('mode')}). You can now /narrate to continue from the intro.")
            state["last_mode"] = "monitor"
            return state
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
        elif intent.action == "end_scene":
            # Auto-persist policy: at scene boundaries, commit staged work in copilot
            flush_res = _auto_flush_if_needed("end_scene")
            persisted_msg = ""
            if isinstance(flush_res, dict) and flush_res.get("ok"):
                persisted_msg = "Staged changes persisted. "
            elif isinstance(flush_res, dict):
                persisted_msg = "Could not persist staged changes now. "
            else:
                persisted_msg = ""

            # Start next scene in the same story
            story_id = state.get("story_id")
            if not story_id:
                _append(state, "assistant", persisted_msg + "Scene ended. No active story to start the next scene.")
                state["last_mode"] = "monitor"
                return state
            next_seq = None
            try:
                if ctx:
                    scenes = query_tool(ctx, "scenes_in_story", story_id=story_id) or []
                    # compute next sequence index; fallback: count + 1
                    seqs = [s.get("sequence_index") for s in scenes if s.get("sequence_index") is not None]
                    if seqs:
                        next_seq = (max(seqs) or 0) + 1
                    else:
                        next_seq = len(scenes) + 1
            except Exception:
                next_seq = None
            new_sc_id = _gen_id("scene")
            deltas = {
                "new_scene": {
                    "id": new_sc_id,
                    "title": f"Scene {next_seq}" if next_seq else None,
                    "story_id": story_id,
                    "sequence_index": next_seq,
                },
                "_draft": f"Start Scene {next_seq or ''}".strip(),
            }
            res = _commit(deltas)
            state["scene_id"] = new_sc_id
            msg = (
                f"Scene ended. {persisted_msg}Started next scene (mode={res.get('mode')}). id={new_sc_id}"
                + (f", seq={next_seq}. " if next_seq else ". ")
                + "Handing off to the narrator to decide the intro and cast."
            )
            _append(state, "assistant", msg)
            # Nudge the router to go to narration on the next turn
            state["override_mode"] = "narration"
            state["last_mode"] = "monitor"
            return state
        elif intent.action == "add_scene":
            uid = state.get("universe_id")
            story_id = intent.story_id or state.get("story_id")
            if not story_id:
                action_reply = "Please specify a story id (e.g., story st:...)."
            else:
                sc_id = _gen_id("scene")
                participants_ids: list[str] = []
                if ctx and intent.participants and uid:
                    for name in intent.participants:
                        try:
                            ent = query_tool(ctx, "entity_by_name_in_universe", universe_id=uid, name=name)
                            if ent:
                                participants_ids.append(ent["id"])  # type: ignore[index]
                        except Exception:
                            pass
                deltas = {
                    "new_scene": {
                        "id": sc_id,
                        "title": intent.name or None,
                        "story_id": story_id,
                        "participants": participants_ids or None,
                    },
                    "facts": ([{"description": intent.description, "occurs_in": sc_id}] if intent.description else None),
                    "_draft": f"Add scene {intent.name or sc_id}",
                }
                res = _commit(deltas)
                # remember last created ids for session continuity
                state["scene_id"] = sc_id
                state["story_id"] = story_id
                action_reply = f"Scene created (mode={res.get('mode')}). id={sc_id}"
        elif intent.action == "modify_last_scene":
            sc_id = state.get("scene_id")
            if not sc_id:
                action_reply = "No last scene in session. Provide scene_id or create a scene first."
            else:
                uid = state.get("universe_id")
                participants_ids: list[str] = []
                if ctx and intent.participants and uid:
                    for name in intent.participants:
                        try:
                            ent = query_tool(ctx, "entity_by_name_in_universe", universe_id=uid, name=name)
                            if ent:
                                participants_ids.append(ent["id"])  # type: ignore[index]
                        except Exception:
                            pass
                facts = []
                if intent.description:
                    facts.append({"description": intent.description, "occurs_in": sc_id})
                deltas = {
                    "scene_id": sc_id,
                    "facts": (facts or None),
                    # Note: adding participants to an existing scene requires updating APPEARS_IN via new_scene participants delta; reuse new_scene path
                    "new_scene": ({"id": sc_id, "participants": participants_ids} if participants_ids else None),
                    "_draft": (intent.description or "Append to scene"),
                }
                res = _commit(deltas)
                action_reply = f"Scene updated (mode={res.get('mode')})."
        elif intent.action == "retcon_entity":
            uid = state.get("universe_id")
            name = (intent.entity_name or "").strip()
            repl = (intent.replacement_name or "").strip() or None
            if not uid or not name:
                action_reply = "Please specify an entity to retcon and current universe."
            else:
                try:
                    # Minimal retcon: write a Fact documenting the change; deep graph surgery is a larger follow-up.
                    desc = f"RETCON: {name} {'→ ' + repl if repl else 'removed from continuity'}."
                    res = _commit({
                        "facts": [{"description": desc, "universe_id": uid}],
                        "_draft": desc[:120],
                    })
                    action_reply = f"Retcon noted (mode={res.get('mode')})."
                except Exception as e:
                    action_reply = f"Error retconning entity: {e}"
        elif intent.action in ("seed_pcs", "seed_npcs"):
            uid = state.get("universe_id")
            if not uid:
                action_reply = "Please set a universe_id first."
            else:
                names = intent.names or []
                if not names:
                    action_reply = "Provide one or more names in quotes, e.g., seed pcs \"Alice\", \"Bob\"."
                else:
                    # Assign IDs so we can link to the current scene if present
                    new_entities = [
                        {"id": _gen_id("entity"), "name": n, "type": intent.kind, "universe_id": uid}
                        for n in names
                    ]
                    deltas = {"new_entities": new_entities, "universe_id": uid, "_draft": f"Seed {intent.kind or 'entity'}s: {', '.join(names[:3])}"}
                    if state.get("scene_id"):
                        deltas["new_scene"] = {"id": state["scene_id"], "participants": [e["id"] for e in new_entities]}
                    res = _commit(deltas)
                    action_reply = f"Seeded {len(new_entities)} {intent.kind or 'entity'}(s) (mode={res.get('mode')})."
        elif intent.action == "create_entity":
            uid = state.get("universe_id")
            if not uid:
                action_reply = "Please set a universe_id first."
            else:
                if not intent.name:
                    action_reply = "Provide a name, e.g., create character \"Logan\" as npc type mutant."
                else:
                    # Distill attributes from description (if provided via 'with ...' in parser in the future) or use entity_type/kind
                    attrs = distill_entity_attributes(intent.description) if intent.description else {}
                    if intent.entity_type:
                        attrs.setdefault("type", intent.entity_type)
                    e_id = _gen_id("entity")
                    new_e = {
                        "id": e_id,
                        "name": intent.name,
                        "type": intent.kind or attrs.get("type"),
                        "universe_id": uid,
                        "attributes": (attrs or None),
                    }
                    deltas = {"new_entities": [new_e], "universe_id": uid, "_draft": f"Create entity {intent.name}"}
                    # Optional linking: story/scene assignment if present in state or intent
                    story_id = intent.story_id or state.get("story_id")
                    scene_id = intent.scene_id or state.get("scene_id")
                    if scene_id:
                        deltas["new_scene"] = {"id": scene_id, "participants": [e_id]}
                    res = _commit(deltas)
                    action_reply = f"Entity created (mode={res.get('mode')})."
        elif intent.action == "save_conversation":
            uid = state.get("universe_id")
            sc_id = state.get("scene_id")
            msgs = state.get("messages") or []
            # Build a compact transcript (last ~30 turns)
            lines = []
            for m in msgs[-60:]:
                r = m.get("role")
                if r in ("user", "assistant"):
                    lines.append(f"{r}: {m.get('content','')}")
            transcript = "\n".join(lines)
            if not transcript.strip():
                action_reply = "No conversation to save."
            else:
                res = _commit({
                    "facts": [{"description": f"TRANSCRIPT\n{transcript}", "universe_id": uid, "occurs_in": sc_id}],
                    "_draft": "Save transcript",
                })
                action_reply = f"Conversation saved (mode={res.get('mode')})."
        elif intent.action == "show_conversation":
            # MVP: retrieve transcript fact(s) for current scene; if none, try universe-level
            uid = state.get("universe_id")
            sc_id = state.get("scene_id")
            try:
                facts = []
                if ctx and sc_id:
                    facts = query_tool(ctx, "facts_for_scene", scene_id=sc_id) or []
                if not facts and ctx and state.get("story_id"):
                    facts = query_tool(ctx, "facts_for_story", story_id=state.get("story_id")) or []
                # filter transcript facts
                transcripts = [f for f in (facts or []) if isinstance(f.get("description"), str) and f.get("description", "").startswith("TRANSCRIPT\n")]
                if transcripts:
                    latest = transcripts[-1]
                    content = latest.get("description", "")[len("TRANSCRIPT\n"):]
                    action_reply = content or "(empty transcript)"
                else:
                    action_reply = "No transcript found for the current scene/story."
            except Exception as e:
                action_reply = f"Error fetching transcript: {e}"

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
