from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.engine.context import ContextToken
from core.engine.orchestrator import (
    Orchestrator,
    OrchestratorConfig,
    build_live_tools,
    flush_staging,
    run_once,
)
from core.engine.steward import StewardService
from core.generation.providers import select_llm_from_env
from core.loaders.agent_prompts import load_agent_prompts

app = FastAPI(title="M.O.N.I.T.O.R. API")


@app.middleware("http")
async def validate_context_token(request: Request, call_next):
    if request.url.path in ["/docs", "/openapi.json", "/"]:
        return await call_next(request)

    token = request.headers.get("X-Context-Token")
    if not token:
        return JSONResponse(status_code=400, content={"error": "Missing X-Context-Token header"})
    try:
        ContextToken.model_validate_json(token)
    except Exception as e:
        return JSONResponse(status_code=422, content={"error": f"Invalid ContextToken: {str(e)}"})
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
    orch = Orchestrator(llm=llm, tools=ctx, config=OrchestratorConfig(mode=req.mode))
    outs: list[dict[str, Any]] = []
    for t in req.turns:
        out = orch.step(t.content, scene_id=t.scene_id)
        outs.append(out)
        if req.persist_each:
            try:
                from core.engine.tools import recorder_tool

                draft = out.get("draft") or t.content
                fact = {"description": (draft[:180] + ("…" if len(draft) > 180 else ""))}
                if t.scene_id:
                    fact["occurs_in"] = t.scene_id
                recorder_tool(ctx, draft=draft, deltas={"facts": [fact], "scene_id": t.scene_id})
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
            fact = {"description": (draft[:180] + ("…" if len(draft) > 180 else ""))}
            if req.scene_id:
                fact["occurs_in"] = req.scene_id
            persisted = recorder_tool(
                ctx, draft=draft, deltas={"facts": [fact], "scene_id": req.scene_id}
            )
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
    """Shallow-by-default deep merge for dicts; lists/atoms are replaced by patch."""
    out: dict[str, Any] = dict(base or {})
    for k, v in (patch or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)  # type: ignore[arg-type]
        else:
            out[k] = v
    return out


class ResolveRequest(BaseModel):
    deltas: dict[str, Any]
    fixes: dict[str, Any] | None = None
    mode: str = "copilot"  # or autopilot
    commit: bool = False  # if True and mode==autopilot, will persist


@app.post("/resolve")
def resolve(req: ResolveRequest):
    # Apply fixes (if any), validate, and optionally commit or stage
    merged = _deep_merge(req.deltas, req.fixes or {})
    will_commit = bool(req.commit and req.mode == "autopilot")
    ctx = build_live_tools(dry_run=(not will_commit))
    svc = StewardService(ctx.query_service)
    ok, warns, errs = svc.validate(merged)
    result: dict[str, Any] = {"ok": ok, "warnings": warns, "errors": errs, "deltas": merged}
    # In copilot or when commit=False, stage via recorder_tool to keep a unified path
    from core.engine.tools import recorder_tool

    if ok:
        commit_out = recorder_tool(ctx, draft="", deltas=merged)
        result["commit"] = commit_out
    else:
        # Still stage in dry-run for traceability
        stage_ctx = build_live_tools(dry_run=True)
        staged = recorder_tool(stage_ctx, draft="", deltas=merged)
        result["commit"] = staged
    return result


@app.post("/staging/flush")
def staging_flush():
    ctx = build_live_tools(dry_run=False)
    res = flush_staging(ctx)
    return res
