from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import sys
from typing import Any

import streamlit as st

# Make repository root importable when running from frontend/
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Avoid module-level imports from project after sys.path mutation; import locally where used.

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
    # Groq mapping (reuse state keys set above for simplicity)
    if st.session_state.get("groq_api_key"):
        os.environ["MONITOR_GROQ_API_KEY"] = st.session_state.get("groq_api_key")
    if st.session_state.get("groq_model"):
        os.environ["MONITOR_GROQ_MODEL"] = st.session_state.get("groq_model")
    elif st.session_state.get("llm_backend") == "groq" and not os.getenv("MONITOR_GROQ_MODEL"):
        os.environ["MONITOR_GROQ_MODEL"] = "llama-3.1-8b-instant"

    # AutoCommit env flag from sidebar
    if st.session_state.get("autocommit_enabled"):
        os.environ["MONITOR_AUTOCOMMIT"] = "1"
    else:
        os.environ.pop("MONITOR_AUTOCOMMIT", None)

    from core.engine.orchestrator import build_live_tools
    from core.generation.providers import select_llm_from_env

    ctx = build_live_tools(dry_run=(mode != "autopilot"))
    llm = select_llm_from_env()
    # Return runtime pieces directly (no Orchestrator wrapper)
    return {"llm": llm, "ctx": ctx}


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
        "llm": None,
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
    st.session_state["llm"] = None
    st.session_state["ctx"] = None
    st.session_state["config_key"] = None


ensure_session_objects()

with st.sidebar:
    st.header("Agents Settings")
    st.session_state.llm_backend = st.selectbox("LLM Backend", ["mock", "openai", "groq"], index=0)
    if st.session_state.llm_backend == "openai":
        st.session_state.openai_api_key = st.text_input("OpenAI API Key", type="password")
        st.session_state.openai_model = st.text_input("Model", value=st.session_state.openai_model)
        st.session_state.openai_base_url = st.text_input(
            "Base URL (optional)", value=st.session_state.openai_base_url
        )
    elif st.session_state.llm_backend == "groq":
        st.session_state.openai_api_key = st.text_input(
            "Groq API Key", type="password", key="groq_api_key"
        )
        # Controls to refresh the models list on demand
        rcols = st.columns([1, 1])
        if rcols[0].button("Refresh models", use_container_width=True, key="refresh_groq_models"):
            st.session_state.pop("_groq_models", None)
            st.session_state.pop("_groq_models_fetched_at", None)
        if st.session_state.get("_groq_models_fetched_at"):
            rcols[1].caption(f"Last updated: {st.session_state['_groq_models_fetched_at']}")
        # Try to fetch models dynamically (cache across reruns for this session)
        default_groq_model = "llama-3.1-8b-instant"
        groq_models = []
        fetch_warn = None
        api_key = (
            st.session_state.get("groq_api_key")
            or os.getenv("MONITOR_GROQ_API_KEY")
            or os.getenv("GROQ_API_KEY")
        )
        if api_key:
            try:
                from core.generation.providers import list_groq_models
                if "_groq_models" not in st.session_state:
                    st.session_state["_groq_models"] = list_groq_models(api_key)
                    # Record timestamp when fetched successfully
                    if st.session_state["_groq_models"]:
                        st.session_state["_groq_models_fetched_at"] = datetime.now().strftime(
                            "%H:%M:%S"
                        )
                groq_models = st.session_state.get("_groq_models") or []
            except Exception as e:  # pragma: no cover
                fetch_warn = f"Could not fetch models dynamically: {e}"
        if not groq_models:
            # Fallback curated list (kept in sync with providers.SUPPORTED_GROQ_MODELS)
            groq_models = [
                "llama-3.1-8b-instant",
                "llama-3.3-70b-versatile",
                "meta-llama/llama-guard-4-12b",
                "openai/gpt-oss-120b",
                "openai/gpt-oss-20b",
                "whisper-large-v3",
                "whisper-large-v3-turbo",
                # Preview
                "deepseek-r1-distill-llama-70b",
                "meta-llama/llama-4-maverick-17b-128e-instruct",
                "meta-llama/llama-4-scout-17b-16e-instruct",
                "meta-llama/llama-prompt-guard-2-22m",
                "meta-llama/llama-prompt-guard-2-86m",
                "moonshotai/kimi-k2-instruct",
                "playai-tts",
                "playai-tts-arabic",
                "qwen/qwen3-32b",
                "compound-beta",
                "compound-beta-mini",
            ]
        if fetch_warn:
            st.caption(fetch_warn)
        elif not api_key:
            st.caption("Set a Groq API key to fetch live models.")
        elif groq_models:
            st.caption(
                f"Loaded {len(groq_models)} models"
                + (
                    f" at {st.session_state.get('_groq_models_fetched_at')}"
                    if st.session_state.get("_groq_models_fetched_at")
                    else ""
                )
            )
        else:
            st.caption("Using fallback model list.")
        # Default selection: prefer the env/session value if it's in the list, else default
        current = (
            st.session_state.get("groq_model")
            or os.getenv("MONITOR_GROQ_MODEL")
            or default_groq_model
        )
        idx = (
            groq_models.index(current)
            if current in groq_models
            else groq_models.index(default_groq_model)
        )
        sel = st.selectbox("Groq Model", options=groq_models, index=idx)
    # For Groq backend, propagate the selected model into session state
    if st.session_state.llm_backend == "groq":
        st.session_state["groq_model"] = sel
    st.session_state.mode = st.radio("Mode", ["copilot", "autopilot"], horizontal=True)
    st.session_state.scene_id = st.text_input(
        "Scene ID (optional)", value=st.session_state.scene_id
    )
    st.session_state.persist_each = st.checkbox(
        "Persist a simple Fact per turn", value=st.session_state.persist_each
    )
    st.session_state.autocommit_enabled = st.checkbox(
        "Auto-commit significant changes (async)",
        value=bool(os.getenv("MONITOR_AUTOCOMMIT") in ("1", "true", "True")),
    )
    st.session_state.force_monitor = st.checkbox(
        "Force monitor intent (send as monitor)", value=False
    )

    cols = st.columns(2)
    if cols[0].button("Reset Session"):
        reset_session()
    if cols[1].button("Flush Staging"):
        if st.session_state.get("ctx") is not None:
            from core.engine.orchestrator import flush_staging
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
                # Validate first
                from core.engine.orchestrator import build_live_tools
                from core.engine.steward import StewardService
                ctx_res = build_live_tools(dry_run=True)
                svc = StewardService(ctx_res.query_service)
                ok, warns, errs = svc.validate(merged)
                # Ask Resolve agent
                from core.engine.resolve_tool import resolve_commit_tool
                from core.generation.providers import select_llm_from_env

                decision = resolve_commit_tool(
                    {
                        "llm": select_llm_from_env(),
                        "deltas": merged,
                        "validations": {"ok": ok, "warnings": warns, "errors": errs},
                        "mode": st.session_state.mode,
                        "hints": {"user_commit": commit_if_ok},
                    }
                )
                agent_commit = bool(decision.get("commit"))
                will_commit = bool(st.session_state.mode == "autopilot" and agent_commit and ok)
                from core.engine.tools import recorder_tool

                if will_commit:
                    from core.engine.orchestrator import build_live_tools
                    commit_ctx = build_live_tools(dry_run=False)
                    commit_out = recorder_tool(commit_ctx, draft="", deltas=merged)
                else:
                    # stage in dry-run for traceability
                    from core.engine.orchestrator import build_live_tools
                    staged_ctx = build_live_tools(dry_run=True)
                    commit_out = recorder_tool(staged_ctx, draft="", deltas=merged)
                st.json(
                    {
                        "ok": ok,
                        "warnings": warns,
                        "errors": errs,
                        "deltas": merged,
                        "decision": decision,
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

    # AutoCommit status panel
    with st.expander("Auto-commit status", expanded=False):
        try:
            from core.engine.orchestrator import autocommit_stats as _ac_stats

            stats = _ac_stats()
            st.json(stats)
        except Exception:
            st.caption("No autocommit status available.")


st.title("MONITOR — Agents Chat")
st.caption("Narrator + Archivist, with copilot/autopilot and optional persistence")

cfg_key = current_config_key()
if st.session_state["config_key"] != cfg_key or st.session_state.get("llm") is None:
    built = build_orchestrator(st.session_state.mode)
    st.session_state["llm"] = built["llm"]
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
    llm = st.session_state["llm"]
    ctx = st.session_state["ctx"]
    # Always defer routing to the agentic backend
    try:
        # If forcing monitor, prepend a prefix the agent router will learn to map to monitor
        msg = (
            user_intent
            if not st.session_state.get("force_monitor")
            else f"[monitor] {user_intent}"
        )
        from core.engine.orchestrator import run_once
        out = run_once(msg, scene_id=scene_id, mode=st.session_state.mode, ctx=ctx, llm=llm)
    except Exception as e:
        # Display a concise, friendly error and keep the session alive
        st.error(f"LLM error: {e}")
        out = {"draft": "", "error": str(e)}

    # Adopt returned references for continuity
    try:
        new_scene = (
            out.get("scene_id")
            or (out.get("refs") or {}).get("scene_id")
            or ((out.get("commit") or {}).get("refs") or {}).get("scene_id")
        )
        if new_scene and isinstance(new_scene, str):
            st.session_state.scene_id = new_scene
    except Exception:
        pass
    # Adopt tags if provided by the flow
    try:
        if out.get("tags") and isinstance(out.get("tags"), list):
            st.session_state["tags"] = list(out.get("tags"))
    except Exception:
        pass

    # Optional lightweight persistence per turn (simple Fact from draft)
    if st.session_state.persist_each:
        try:
            from core.engine.tools import recorder_tool

            draft = out.get("draft") or user_intent
            fact = {"description": (draft[:180] + ("…" if len(draft) > 180 else ""))}
            occurs_in = st.session_state.scene_id or scene_id
            if occurs_in:
                fact["occurs_in"] = occurs_in
            commit = {"facts": [fact], "scene_id": occurs_in}
            persisted = recorder_tool(ctx, draft=draft, deltas=commit)
            out["persisted"] = persisted
        except Exception as e:  # pragma: no cover
            out["persist_error"] = str(e)

    st.session_state["history"].append({"intent": user_intent, **out})
    st.rerun()
