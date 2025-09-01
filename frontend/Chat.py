from __future__ import annotations

import json
import os
from typing import Any

import streamlit as st

from core.engine.orchestrator import (
    Orchestrator,
    OrchestratorConfig,
    build_live_tools,
    flush_staging,
)
from core.engine.steward import StewardService
from core.generation.providers import select_llm_from_env

st.set_page_config(page_title="MONITOR — Agents Chat", layout="wide")


def build_orchestrator(mode: str) -> dict[str, Any]:
    # Ensure env reflects current sidebar configuration for provider selection
    os.environ["MONITOR_LLM_BACKEND"] = st.session_state.get("llm_backend", "mock")
    if st.session_state.get("openai_api_key"):
        os.environ["MONITOR_OPENAI_API_KEY"] = st.session_state.get("openai_api_key")
    if st.session_state.get("openai_model"):
        os.environ["MONITOR_OPENAI_MODEL"] = st.session_state.get("openai_model")
    if st.session_state.get("openai_base_url"):
        os.environ["MONITOR_OPENAI_BASE_URL"] = st.session_state.get("openai_base_url")

    ctx = build_live_tools(dry_run=(mode != "autopilot"))
    llm = select_llm_from_env()
    orch = Orchestrator(llm=llm, tools=ctx, config=OrchestratorConfig(mode=mode))
    return {"orch": orch, "ctx": ctx}


def ensure_session_objects():
    defaults = {
        "llm_backend": "mock",
        "openai_api_key": "",
        "openai_model": "gpt-4o-mini",
        "openai_base_url": "",
        "mode": "copilot",
        "scene_id": "",
        "persist_each": False,
        "history": [],
        "config_key": None,
        "orch": None,
        "ctx": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(base or {})
    for k, v in (patch or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)  # type: ignore[arg-type]
        else:
            out[k] = v
    return out


def current_config_key() -> str:
    return ":".join(
        [
            st.session_state.get("llm_backend", "mock"),
            st.session_state.get("openai_model", ""),
            "autopilot" if st.session_state.get("mode") == "autopilot" else "copilot",
        ]
    )


def reset_session():
    st.session_state["history"] = []
    st.session_state["orch"] = None
    st.session_state["ctx"] = None
    st.session_state["config_key"] = None


ensure_session_objects()

with st.sidebar:
    st.header("Agents Settings")
    st.session_state.llm_backend = st.selectbox("LLM Backend", ["mock", "openai"], index=0)
    if st.session_state.llm_backend == "openai":
        st.session_state.openai_api_key = st.text_input("OpenAI API Key", type="password")
        st.session_state.openai_model = st.text_input("Model", value=st.session_state.openai_model)
        st.session_state.openai_base_url = st.text_input(
            "Base URL (optional)", value=st.session_state.openai_base_url
        )
    st.session_state.mode = st.radio("Mode", ["copilot", "autopilot"], horizontal=True)
    st.session_state.scene_id = st.text_input(
        "Scene ID (optional)", value=st.session_state.scene_id
    )
    st.session_state.persist_each = st.checkbox(
        "Persist a simple Fact per turn", value=st.session_state.persist_each
    )

    cols = st.columns(2)
    if cols[0].button("Reset Session"):
        reset_session()
    if cols[1].button("Flush Staging"):
        if st.session_state.get("ctx") is not None:
            out = flush_staging(st.session_state["ctx"])  # type: ignore
            st.toast(f"Flush: {out}")

    with st.expander("Resolve / Commit Deltas", expanded=False):
        st.caption("Validate deltas, apply optional fixes, and stage or commit based on mode.")
        deltas_text = st.text_area("Deltas (JSON)", height=160, key="resolve_deltas_text")
        fixes_text = st.text_area("Fixes (JSON, optional)", height=120, key="resolve_fixes_text")
        commit_if_ok = st.checkbox("Commit if Autopilot", value=False, key="resolve_commit")
        if st.button("Resolve"):
            try:
                deltas = json.loads(deltas_text) if deltas_text.strip() else {}
            except Exception as e:
                st.error(f"Invalid deltas JSON: {e}")
                deltas = None
            try:
                fixes = json.loads(fixes_text) if fixes_text.strip() else None
            except Exception as e:
                st.error(f"Invalid fixes JSON: {e}")
                fixes = None
            if deltas is not None:
                merged = _deep_merge(deltas, fixes or {})
                will_commit = bool(commit_if_ok and st.session_state.mode == "autopilot")
                ctx_res = build_live_tools(dry_run=(not will_commit))
                svc = StewardService(ctx_res.query_service)
                ok, warns, errs = svc.validate(merged)
                from core.engine.tools import recorder_tool

                if ok:
                    commit_out = recorder_tool(ctx_res, draft="", deltas=merged)
                else:
                    # stage in dry-run for traceability
                    staged_ctx = build_live_tools(dry_run=True)
                    commit_out = recorder_tool(staged_ctx, draft="", deltas=merged)
                st.json(
                    {
                        "ok": ok,
                        "warnings": warns,
                        "errors": errs,
                        "deltas": merged,
                        "commit": commit_out,
                    }
                )
        # Show current staging buffer size if available
        try:
            ctx0 = st.session_state.get("ctx")
            if ctx0 and getattr(ctx0, "staging", None) is not None:
                st.caption(f"Staging pending: {ctx0.staging.pending()} items")
        except Exception:
            pass


st.title("MONITOR — Agents Chat")
st.caption("Narrator + Archivist, with copilot/autopilot and optional persistence")

cfg_key = current_config_key()
if st.session_state["config_key"] != cfg_key or st.session_state.get("orch") is None:
    built = build_orchestrator(st.session_state.mode)
    st.session_state["orch"] = built["orch"]
    st.session_state["ctx"] = built["ctx"]
    st.session_state["config_key"] = cfg_key

# Chat history display
for turn in st.session_state["history"]:
    with st.chat_message("user"):
        st.markdown(turn["intent"])  # user prompt
    with st.chat_message("assistant"):
        st.markdown(turn["draft"])  # agent draft
        with st.expander("Details"):
            st.json({k: v for k, v in turn.items() if k not in ("intent", "draft")})


# Input box
user_intent = st.chat_input("Write your next beat…")
if user_intent:
    scene_id = st.session_state.scene_id or None
    orch: Orchestrator = st.session_state["orch"]
    ctx = st.session_state["ctx"]
    out = orch.step(user_intent, scene_id=scene_id)

    # Optional lightweight persistence per turn (simple Fact from draft)
    if st.session_state.persist_each:
        try:
            from core.engine.tools import recorder_tool

            draft = out.get("draft") or user_intent
            fact = {"description": (draft[:180] + ("…" if len(draft) > 180 else ""))}
            if scene_id:
                fact["occurs_in"] = scene_id
            commit = {"facts": [fact], "scene_id": scene_id}
            persisted = recorder_tool(ctx, draft=draft, deltas=commit)
            out["persisted"] = persisted
        except Exception as e:  # pragma: no cover
            out["persist_error"] = str(e)

    st.session_state["history"].append(
        {
            "intent": user_intent,
            **out,
        }
    )
    st.experimental_rerun()
