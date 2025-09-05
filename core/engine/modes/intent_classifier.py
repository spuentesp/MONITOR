"""Intent classification for determining conversation mode."""

from __future__ import annotations

import json

from core.engine.monitor_parser import parse_monitor_intent
from core.generation.providers import select_llm_from_env

from .constants import CMD_MONITOR, CMD_NARRATE
from .graph_state import GraphState


def classify_intent(state: GraphState) -> GraphState:
    """Classify user intent and determine conversation mode.

    Returns updated state with mode, confidence, and reasoning.
    """
    text = state.get("input", "").strip()
    override = state.get("override_mode")

    # Handle explicit overrides
    if override in ("narration", "monitor"):
        state["mode"] = override
        meta = state.get("meta") or {}
        meta.update({"router": {"confidence": 1.0, "reason": "override", "decided": override}})
        state["meta"] = meta
        return state

    # Check for explicit commands
    mode = "narration"  # default
    confidence = 0.6
    reason = "default"

    if CMD_MONITOR.match(text):
        mode, confidence, reason = "monitor", 1.0, "explicit_cmd"
    elif CMD_NARRATE.match(text):
        mode, confidence, reason = "narration", 1.0, "explicit_cmd"
    elif parse_monitor_intent(text):
        mode, confidence, reason = "monitor", 0.9, "parsed_intent"
    else:
        # Use LLM for classification
        mode, confidence, reason = _classify_with_llm(text, confidence, reason)

    state["mode"] = mode
    meta = state.get("meta") or {}
    meta.update({"router": {"confidence": confidence, "reason": reason, "decided": mode}})
    state["meta"] = meta
    return state


def _classify_with_llm(
    text: str, default_confidence: float, default_reason: str
) -> tuple[str, float, str]:
    """Use LLM to classify intent when patterns don't match."""
    try:
        llm = select_llm_from_env()
        prompt = f'''Classify this user input as either "narration" or "monitor":

Input: "{text}"

- "narration": Creative storytelling, character interactions, world-building
- "monitor": Operational commands, data queries, system management

Respond with JSON: {{"intent": "narration|monitor", "confidence": 0.0-1.0, "reason": "brief explanation"}}'''

        out = llm.complete(
            system_prompt="You are a precise intent classifier. Return only valid JSON.",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=100,
        )

        data = json.loads(out) if isinstance(out, str) else {}
        lm_intent = str(data.get("intent", "")).lower()
        lm_conf = float(data.get("confidence", 0.0))
        lm_reason = str(data.get("reason", ""))

        if lm_intent in ("narration", "monitor") and lm_conf >= default_confidence:
            return lm_intent, lm_conf, f"llm:{lm_reason}"

    except Exception:
        pass

    return "narration", default_confidence, default_reason
