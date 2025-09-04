from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core.engine.modes.graph_state import GraphState
from core.engine.modes.graph_builder import build_langgraph_modes
from core.engine.orchestrator import build_live_tools

router = APIRouter(tags=["langgraph-modes"])

_graph = build_langgraph_modes()
_SESSIONS: dict[str, GraphState] = {}


class ChatReq(BaseModel):
    session_id: str = Field(..., description="ID de sesión del usuario")
    message: str = Field(..., description="Mensaje del usuario")
    universe_id: str | None = Field(None, description="Universo activo")
    override: str | None = Field(None, description="Forzar 'narration' o 'monitor'")
    mode: str = Field(
        "copilot", description="'copilot' (dry-run/staging) o 'autopilot' (persistir)"
    )


class ChatRes(BaseModel):
    mode: str
    reply: str
    meta: dict


@router.post("/langgraph/modes/chat", response_model=ChatRes)
def chat(req: ChatReq, request: Request) -> ChatRes:
    state = _SESSIONS.get(req.session_id) or {"messages": [], "last_mode": "narration"}
    state["input"] = req.message
    state["session_id"] = req.session_id
    if req.universe_id:
        state["universe_id"] = req.universe_id
    if req.override in ("narration", "monitor"):
        state["override_mode"] = req.override  # solo para este turno
    else:
        state.pop("override_mode", None)

    # Inyecta ToolContext
    # Construye ToolContext con o sin persistencia según modo
    tools = build_live_tools(dry_run=(req.mode != "autopilot"))
    # Extrae ContextToken del header si existe para omniverse/multiverse/universe
    try:
        token_raw = request.headers.get("X-Context-Token")
        if token_raw:
            import json as _json

            tok = _json.loads(token_raw)
            # Enforce write permission for autopilot requests
            if str(req.mode).lower() == "autopilot" and tok.get("mode") != "write":
                raise HTTPException(
                    status_code=403, detail="Autopilot writes require ContextToken.mode=write"
                )
            for k in ("omniverse_id", "multiverse_id", "universe_id"):
                if tok.get(k):
                    state[k] = tok[k]
    except Exception:
        pass
    state["tools"] = tools  # type: ignore[index]

    out: GraphState = _graph.invoke(state)

    # Extrae última respuesta
    messages = out.get("messages", [])
    reply = ""
    for m in reversed(messages):
        if m.get("role") == "assistant":
            reply = m.get("content", "")
            break
    if not reply:
        raise HTTPException(status_code=500, detail="No reply generated")

    # Persiste sesión (limpiando input y override efímeros)
    cleaned: dict[str, Any] = {
        k: v for k, v in out.items() if k not in ("input", "override_mode", "tools")
    }
    _SESSIONS[req.session_id] = cleaned
    return ChatRes(mode=out.get("mode", "narration"), reply=reply, meta=out.get("meta", {}))


class HelpRes(BaseModel):
    help: str


@router.get("/langgraph/modes/help", response_model=HelpRes)
def help_endpoint() -> HelpRes:
    from core.engine.modes.constants import HELP_TEXT

    return HelpRes(help=HELP_TEXT)
