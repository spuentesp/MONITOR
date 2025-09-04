"""Router logic for determining execution mode."""
from __future__ import annotations

import json
import re

from core.generation.providers import select_llm_from_env
from .state import GraphState, Mode

# Command patterns
_CMD_MONITOR = re.compile(r"^[\s]*[\/@]?(monitor)\b", re.IGNORECASE)
_CMD_NARRATE = re.compile(r"^[\s]*[\/@]?(narrar|narrador|narrate|narrator)\b", re.IGNORECASE)
_CMD_HELP = re.compile(r"^[\s]*[\/@]?help\b", re.IGNORECASE)


def get_help_text() -> str:
    """Return help text for available commands."""
    return (
        "Comandos disponibles (prefijo opcional / o @):\n"
        "- /help: muestra este mensaje de ayuda.\n"
        "- /monitor <pedido>: fuerza modo Monitor para administración (crear/actualizar/consultar).\n"
        "- /narrar <mensaje>: fuerza modo Narración para continuar la historia.\n"
        '- /monitor iniciar universo [<id>] [nombre "..."] [multiverso <id>]: asistente para crear un universo listo para narrar.\n'
        "Consultas útiles (EN): list multiverses | list universes [multiverse <id>] | list stories [universe <id>] | show 'Tony Stark' in universe <id> | enemies of 'Rogue' in universe <id> | last time they saw 'Deadpool' in universe <id>.\n"
        'GM onboarding: start a new story [topics "urban fantasy, heists"] [story "Night Shift"] | save conversation | end scene.\n'
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
        meta.update(
            {"router": {"confidence": 1.0, "reason": f"override:{override}", "decided": override}}
        )
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
    elif any(
        k in t.lower()
        for k in [
            "monitor:",
            "administra",
            "configura",
            "crea",
            "actualiza",
            "consulta",
            "borra",
            "persistir",
            "guardar",
            "dataset",
            "índice",
            "indice",
            "vector",
            "embedding",
        ]
    ):
        mode, reason, confidence = "monitor", "keywords", 0.75
    elif any(
        k in t.lower()
        for k in [
            "cuenta",
            "narra",
            "qué pasó",
            "que paso",
            "continúa",
            "continua",
            "siguiente capítulo",
            "siguiente capitulo",
            "rol",
            "personaje",
        ]
    ):
        mode, reason, confidence = "narration", "keywords", 0.7

    # Clasificador LLM (refina decisión) – robusto a backend mock
    try:
        llm = select_llm_from_env()
        sys = (
            "Clasifica el mensaje como 'narration' (historia diegética) o 'monitor' "
            "(operaciones del sistema: crear/actualizar/consultar, admin, ERPs, APIs). "
            'Responde SOLO JSON: {"intent":"narration|monitor","confidence":0.0-1.0,"reason":"..."}.'
        )
        user = f"Mensaje: {text}\nÚltimo modo: {last_mode}"
        out = llm.complete(
            system_prompt=sys,
            messages=[{"role": "user", "content": user}],
            temperature=0.0,
            max_tokens=120,
        )
        data = json.loads(out) if isinstance(out, str) else {}
        lm_intent = str(data.get("intent", "")).lower()
        lm_conf = float(data.get("confidence", 0.0))
        lm_reason = str(data.get("reason", ""))
        if lm_intent in ("narration", "monitor") and (
            lm_conf >= confidence or reason == "fallback"
        ):
            mode, confidence, reason = lm_intent, lm_conf, f"llm:{lm_reason}"
    except Exception:
        pass

    state["mode"] = mode
    meta = state.get("meta") or {}
    meta.update({"router": {"confidence": confidence, "reason": reason, "decided": mode}})
    state["meta"] = meta
    return state
