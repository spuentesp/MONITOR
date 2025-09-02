from __future__ import annotations

from typing import Any, Dict

import json
from core.agents.resolve import resolve_agent


def resolve_commit_tool(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool: Ask Resolve agent whether to commit now.

    Args context may include:
      - deltas: list/object of changes proposed
      - validations: checks/critic results
      - mode: "strict"|"lenient"|... from env
      - hints: optional user hint or conductor suggestion
    Returns: { commit: bool, reason: str, fixes?: object }
    """
    llm = context.get("llm")
    payload = {
        "deltas": context.get("deltas"),
        "validations": context.get("validations"),
        "mode": context.get("mode"),
        "hints": context.get("hints"),
    }
    agent = resolve_agent(llm)
    try:
        reply_text = agent.act([{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}])
    except Exception as e:
        return {"commit": False, "reason": f"resolve_agent_error: {e}"}

    # Normalize defensively
    decision: Dict[str, Any] = {"commit": False, "reason": "undecided"}
    try:
        obj = json.loads(reply_text) if isinstance(reply_text, str) else {}
        if isinstance(obj, dict):
            decision.update(obj)
    except Exception as e:
        decision = {"commit": False, "reason": f"resolve_error: {e}"}
    # Fail-open in autopilot if validations are ok and agent didn't produce a usable JSON decision
    try:
        mode = (context.get("mode") or "").lower()
        vals = context.get("validations") or {}
        if not bool(decision.get("commit")) and mode == "autopilot" and bool(vals.get("ok", False)):
            decision = {"commit": True, "reason": "autopilot_default"}
    except Exception:
        pass
    return decision
