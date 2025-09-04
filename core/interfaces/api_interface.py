from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.engine.context import ContextToken
from core.engine.orchestrator import (
    build_live_tools,
    flush_staging,
    run_once,
)
from core.engine.resolve_tool import resolve_commit_tool
from core.engine.steward import StewardService
from core.generation.providers import select_llm_from_env
from core.interfaces.branches_api import router as branches_router
from core.interfaces.langgraph_modes_api import router as langgraph_modes_router
from core.loaders.agent_prompts import load_agent_prompts
from core.utils.merge import deep_merge
from core.utils.persist import persist_simple_fact_args

app = FastAPI(title="M.O.N.I.T.O.R. API")


@app.middleware("http")
async def validate_context_token(request: Request, call_next):
    if request.url.path in ["/docs", "/openapi.json", "/", "/health"]:
        return await call_next(request)

    token = request.headers.get("X-Context-Token")
    if not token:
        return JSONResponse(status_code=400, content={"error": "Missing X-Context-Token header"})
    try:
        tok = ContextToken.model_validate_json(token)
    except Exception as e:
        return JSONResponse(status_code=422, content={"error": f"Invalid ContextToken: {str(e)}"})
    # Enforce write mode for endpoints that can commit when mode=autopilot
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        # If the request body indicates autopilot, require tok.mode == 'write'
        try:
            if request.headers.get("content-type", "").startswith("application/json"):
                body = await request.json()
                req_mode = str((body or {}).get("mode") or "").lower()
                if req_mode == "autopilot" and tok.mode != "write":
                    return JSONResponse(status_code=403, content={"error": "Autopilot writes require ContextToken.mode=write"})
        except Exception:
            # If we can't parse body, fail closed only for explicit autopilot endpoints; otherwise continue
            pass
    return await call_next(request)


@app.get("/")
def root():
    return {"message": "M.O.N.I.T.O.R. backend operativo"}


@app.get("/config/agents")
def get_agent_prompts():
    return load_agent_prompts()


@app.get("/health")
def health():
    return {"ok": True}


# LangGraph Modes (Narrator vs Monitor)
app.include_router(langgraph_modes_router, prefix="/api")

# Branching & cloning API
app.include_router(branches_router, prefix="/api")


# --- Minimal Chat API ---


class ChatTurn(BaseModel):
    content: str
    scene_id: str | None = None


class ChatRequest(BaseModel):
    turns: list[ChatTurn]
    mode: str = "copilot"  # or autopilot
    persist_each: bool = False


class StepRequest(BaseModel):
    intent: str
    scene_id: str | None = None
    mode: str = "copilot"
    record_fact: bool = False


@app.post("/chat")
def chat(req: ChatRequest):
    llm = select_llm_from_env()
    ctx = build_live_tools(dry_run=(req.mode != "autopilot"))
    outs: list[dict[str, Any]] = []
    for t in req.turns:
        out = run_once(t.content, scene_id=t.scene_id, mode=req.mode, ctx=ctx, llm=llm)
        outs.append(out)
        if req.persist_each:
            try:
                from core.engine.tools import recorder_tool

                draft = out.get("draft") or t.content
                deltas = persist_simple_fact_args(draft, t.scene_id)
                recorder_tool(ctx, draft=draft, deltas=deltas)
            except Exception:
                pass
    return {"steps": outs}


@app.post("/step")
def step(req: StepRequest):
    out = run_once(req.intent, scene_id=req.scene_id, mode=req.mode)
    if req.record_fact:
        ctx = build_live_tools(dry_run=(req.mode != "autopilot"))
        try:
            from core.engine.tools import recorder_tool

            draft = out.get("draft") or req.intent
            deltas = persist_simple_fact_args(draft, req.scene_id)
            persisted = recorder_tool(ctx, draft=draft, deltas=deltas)
            out["persisted"] = persisted
        except Exception:
            pass
    return out


class ValidateRequest(BaseModel):
    deltas: dict[str, Any]


@app.post("/validate")
def validate(req: ValidateRequest):
    ctx = build_live_tools(dry_run=True)
    svc = StewardService(ctx.query_service)
    ok, warns, errs = svc.validate(req.deltas)
    return {"ok": ok, "warnings": warns, "errors": errs}


# --- Interactive validation/fix/commit helpers ---


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    # Back-compat shim: use shared util
    return deep_merge(base, patch)


class ResolveRequest(BaseModel):
    deltas: dict[str, Any]
    fixes: dict[str, Any] | None = None
    mode: str = "copilot"  # or autopilot
    commit: bool = False  # if True and mode==autopilot, will persist


@app.post("/resolve")
def resolve(req: ResolveRequest):
    # Apply fixes (if any)
    merged = deep_merge(req.deltas, req.fixes or {})
    # Always validate before asking the agent
    dry_by_mode = not (req.mode == "autopilot")
    ctx = build_live_tools(dry_run=dry_by_mode)
    svc = StewardService(ctx.query_service)
    ok, warns, errs = svc.validate(merged)
    # Ask Resolve agent to decide commit vs stage; default is stage
    try:
        from core.generation.providers import select_llm_from_env

        llm = select_llm_from_env()
    except Exception:
        llm = None
    decision = resolve_commit_tool(
        {
            "llm": llm,
            "deltas": merged,
            "validations": {"ok": ok, "warnings": warns, "errors": errs},
            "mode": req.mode,
            "hints": {"user_commit": req.commit},
        }
    )
    agent_commit = bool(decision.get("commit"))
    # Only allow commit when autopilot AND agent approves AND validations ok
    will_commit = bool((req.mode == "autopilot") and agent_commit and ok)

    from core.engine.tools import recorder_tool

    if ok and will_commit:
        # Persist immediately in autopilot per agent decision
        commit_ctx = build_live_tools(dry_run=False)
        commit_out = recorder_tool(commit_ctx, draft="", deltas=merged)
    else:
        # Stage in dry-run for traceability
        stage_ctx = build_live_tools(dry_run=True)
        commit_out = recorder_tool(stage_ctx, draft="", deltas=merged)
    return {
        "ok": ok,
        "warnings": warns,
        "errors": errs,
        "deltas": merged,
        "decision": decision,
        "commit": commit_out,
    }


@app.post("/staging/flush")
def staging_flush():
    ctx = build_live_tools(dry_run=False)
    res = flush_staging(ctx)
    return res
