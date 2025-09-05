"""Core monitor actions and data operations."""

from __future__ import annotations

from core.engine.tools import ToolContext, recorder_tool
from core.generation.interfaces.llm import Message
from core.generation.providers import select_llm_from_env

from .graph_state import GraphState


def commit_deltas(state: GraphState, deltas: dict) -> dict:
    """Commit changes using the recorder tool."""
    ctx: ToolContext | None = state.get("tools")  # type: ignore[assignment]
    if not ctx:
        return {"mode": "noop", "reason": "no_tool_context"}

    draft = deltas.get("_draft", "")
    return recorder_tool(
        ctx, draft=draft, deltas={k: v for k, v in deltas.items() if k != "_draft"}
    )


def auto_flush_if_needed(state: GraphState, reason: str) -> dict | None:
    """Auto-flush staged changes at safe boundaries if in dry_run mode."""
    ctx: ToolContext | None = state.get("tools")  # type: ignore[assignment]

    try:
        if ctx and getattr(ctx, "dry_run", True):
            # Lazy import to avoid circulars
            from core.engine.orchestrator import flush_staging

            return flush_staging(ctx)  # type: ignore[arg-type]
    except Exception:
        return {"ok": False, "error": "auto_flush_failed"}

    return None


def generate_llm_response(state: GraphState, text: str) -> str:
    """Generate a default LLM response for operational queries."""
    llm = select_llm_from_env()

    system_prompt = (
        "Eres el Monitor, un asistente operacional. Responde breve, preciso y accionable. "
        "No escribas narrativa. Si la petición requiere ejecutar acciones reales "
        "(crear/actualizar/consultar universos, multiversos, datos), "
        "propón un plan de 2-3 pasos y confirma los datos faltantes."
    )

    msgs: list[Message] = (state.get("messages") or []) + [{"role": "user", "content": text}]

    return llm.complete(
        system_prompt=system_prompt, messages=msgs[-8:], temperature=0.2, max_tokens=350
    )
