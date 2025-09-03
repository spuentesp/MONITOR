from __future__ import annotations

import json
import os
from typing import Any

from core.engine.resolve_tool import resolve_commit_tool


def _env_flag(name: str, default: str = "0") -> bool:
    """Parse common boolean-ish env flags once.

    Accepts 1/true/True as truthy; everything else is false.
    """
    return os.getenv(name, default) in ("1", "true", "True")


def build_langgraph_flow(tools: Any, config: dict | None = None):
    """Build a minimal LangGraph flow using existing tools.

    This function avoids importing langgraph at module import time to keep it optional.
    """
    try:
        from langgraph.graph import END, StateGraph
    except Exception as e:
        raise RuntimeError("LangGraph is not installed. Please install langgraph.") from e

    # Optional LangChain tools (env-gated)
    cfg = config or {}
    lc_tools = None
    use_lc_tools = bool(cfg.get("use_lc_tools", _env_flag("MONITOR_LC_TOOLS", "0")))
    if use_lc_tools:
        try:
            from core.engine.lc_tools import build_langchain_tools

            lc_list = build_langchain_tools(tools["ctx"])  # returns a list of Tool objects
            lc_tools = {t.name: t for t in lc_list}
        except Exception:
            lc_tools = None

    # Simple state for demonstration
    class State(dict):
        pass

    def _safe_act(agent_key: str, messages: list[dict[str, Any]], default: Any = None) -> Any:
        """Call tools[agent_key].act(messages) defensively.

        Returns default on error or missing agent.
        """
        try:
            agent = tools.get(agent_key)
            if agent:
                return agent.act(messages)
        except Exception:
            pass
        return default

    def _fetch_relations(scene_id: str) -> list[dict[str, Any]]:
        """Retrieve relations effective in scene via lc_tools (if enabled) or query_tool.

        Returns a list; errors are swallowed to keep flow resilient.
        """
        try:
            if lc_tools and "query_tool" in lc_tools:
                rels = lc_tools["query_tool"].invoke(
                    {"method": "relations_effective_in_scene", "scene_id": scene_id}
                )
            else:
                rels = tools["query_tool"](
                    tools["ctx"], "relations_effective_in_scene", scene_id=scene_id
                )
            return rels or []
        except Exception:
            return []

    def intent_router(state: dict[str, Any]) -> dict[str, Any]:
        # Let LLM route the input. In strict mode, avoid assuming narrative.
        intent = state.get("intent", "")
        routed = _safe_act("intent_router", [{"role": "user", "content": intent}], default=None)
        label = (routed or "").strip().lower() if isinstance(routed, str) else ""
        if not label and _env_flag("MONITOR_AGENTIC_STRICT", "0"):
            label = "qa"  # minimal safe default
        if not label:
            label = "narrative"
        return {**state, "intent_type": label}

    def director(state: dict[str, Any]) -> dict[str, Any]:
        # Use LLM-backed Director if provided; fallback to trivial plan
        intent = state.get("intent", "")
        reply = _safe_act(
            "director",
            [{"role": "user", "content": f"Intent: {intent}. Return a tiny plan."}],
            default=None,
        )
        if reply is not None:
            # Ensure a structured plan for callers/tests even if LLM returns free text
            structured = {"beats": [intent] if intent else [], "assumptions": []}
            if isinstance(reply, str) and reply.strip():
                structured["notes"] = reply.strip()
            elif isinstance(reply, dict):
                # Merge any dict reply but keep required keys
                structured.update(reply)
                structured.setdefault("beats", [intent] if intent else [])
                structured.setdefault("assumptions", [])
            return {**state, "plan": structured}
        return {**state, "plan": {"beats": [intent], "assumptions": []}}

    def librarian(state: dict[str, Any]) -> dict[str, Any]:
        scene_id = state.get("scene_id")
        evidence = []
        if scene_id:
            rels = _fetch_relations(scene_id)
            if rels is not None:
                evidence.append({"relations": rels})
        # Optionally let LLM librarian summarize evidence
        if evidence:
            summary = _safe_act(
                "librarian",
                [{"role": "user", "content": f"Summarize briefly: {str(evidence)[:800]}"}],
                default=None,
            )
            if summary is not None:
                return {**state, "evidence": evidence, "evidence_summary": summary}
        return {**state, "evidence": evidence}

    def steward(state: dict[str, Any]) -> dict[str, Any]:
        # LLM-backed steward for quick validation hints
        hints = _safe_act(
            "steward",
            [
                {
                    "role": "user",
                    "content": (
                        f"Validate plan and draft context: "
                        f"{str({k: v for k, v in state.items() if k in ['plan', 'evidence']})[:800]}"
                    ),
                }
            ],
            default=None,
        )
        if hints is not None:
            return {**state, "validation": {"ok": True, "warnings": [hints]}}
        return {**state, "validation": {"ok": True, "warnings": []}}

    def _tool_schema() -> list[dict[str, Any]]:
        return [
            {
                "name": "bootstrap_story",
                "args": {
                    "title": "str",
                    "protagonist_name": "str?",
                    "time_label": "str?",
                    "tags": "list[str]?",
                    "universe_id": "str?",
                },
                "returns": {"refs": {"scene_id": "str", "story_id": "str", "universe_id": "str"}},
            },
            {
                "name": "query",
                "args": {
                    "method": "str",
                    "scene_id": "str?",
                    "story_id": "str?",
                    "universe_id": "str?",
                },
                "returns": "any",
            },
            {
                "name": "recorder",
                "args": {
                    "facts": "list[Fact]?",
                    "relations": "list[Relation]?",
                    "relation_states": "list[RelationState]?",
                    "scene_id": "str?",
                },
                "returns": {"mode": "str", "refs": {"scene_id": "str?", "run_id": "str"}},
            },
            {
                "name": "narrative",
                "args": {"op": "str", "payload": "dict"},
                "returns": {"ok": "bool", "mode": "str"},
            },
            {
                "name": "object_upload",
                "args": {
                    "bucket": "str",
                    "key": "str",
                    "data_b64": "str",
                    "filename": "str",
                    "content_type": "str?",
                    "universe_id": "str",
                    "story_id": "str?",
                    "scene_id": "str?",
                },
                "returns": {"ok": "bool", "mode": "str"},
            },
        ]

    def planner(state: dict[str, Any]) -> dict[str, Any]:
        """Agentic planner: always request a JSON list of actions; empty list means no-ops.

        The planner decides if/what to do given intent and context.
        """
        # Provide richer but compact context: IDs and librarian/evidence summary if available
        compact_ctx = {
            k: state.get(k)
            for k in ("scene_id", "story_id", "universe_id", "tags")
            if state.get(k) is not None
        }
        if state.get("evidence_summary"):
            compact_ctx["evidence_summary"] = state.get("evidence_summary")
        plan = _safe_act(
            "planner",
            [
                {
                    "role": "user",
                    "content": f"Intent: {state.get('intent')}\nContext: {compact_ctx}\nTools: {_tool_schema()}\nReturn JSON array of actions.",
                }
            ],
            default="[]",
        )
        try:
            actions = json.loads(plan) if isinstance(plan, str) else plan
        except Exception:
            actions = []
        return {**state, "actions": actions or []}

    def execute_actions(state: dict[str, Any]) -> dict[str, Any]:
        actions = state.get("actions") or []
        ctx = tools["ctx"]
        results: list[dict[str, Any]] = []
        new_scene_id: str | None = None
        new_story_id: str | None = None
        new_universe_id: str | None = None
        new_tags: list[str] | None = None
        evidence_accum: list[dict[str, Any]] = []
        narrative_result: dict[str, Any] | None = None
        for act in actions:
            try:
                tool = (act or {}).get("tool")
                args = (act or {}).get("args") or {}
                if tool == "bootstrap_story":
                    res = tools["bootstrap_story_tool"](ctx, **args)
                    try:
                        new_scene_id = (
                            (res.get("refs") or {}).get("scene_id")
                            or (res.get("result") or {}).get("scene_id")
                            or new_scene_id
                        )
                        new_story_id = (
                            (res.get("refs") or {}).get("story_id")
                            or (res.get("result") or {}).get("story_id")
                            or new_story_id
                        )
                        new_universe_id = (
                            (res.get("refs") or {}).get("universe_id")
                            or (res.get("result") or {}).get("universe_id")
                            or new_universe_id
                        )
                    except Exception:
                        pass
                    try:
                        # Capture tags from args to seed continuity across nodes
                        if isinstance(args.get("tags"), list):
                            new_tags = list(args.get("tags"))
                        # Include time_label tag if provided
                        if args.get("time_label"):
                            if new_tags is None:
                                new_tags = []
                            if args["time_label"] not in new_tags:
                                new_tags.append(args["time_label"])
                    except Exception:
                        pass
                elif tool == "recorder":
                    res = tools["recorder_tool"](ctx, draft="", deltas=args)
                elif tool == "query":
                    res = tools["query_tool"](ctx, **args)
                elif tool == "narrative":
                    payload = args.get("payload") or {}
                    # If we have evidence from prior retrieval, inject citations into meta
                    if evidence_accum and "meta" not in payload:
                        payload["meta"] = {"citations": evidence_accum}
                    res = tools["narrative_tool"](
                        ctx, args.get("op"), llm=tools.get("llm"), **payload
                    )
                    if isinstance(res, dict):
                        narrative_result = res
                elif tool == "indexing":
                    # args must include vector_collection, text_index, docs
                    res = tools["indexing_tool"](ctx, llm=tools.get("llm"), **args)
                elif tool == "retrieval":
                    res = tools["retrieval_tool"](ctx, **args)
                    try:
                        hits = (res or {}).get("results") or []
                        if isinstance(hits, list):
                            evidence_accum.extend(hits)
                    except Exception:
                        pass
                elif tool == "object_upload":
                    res = tools["object_upload_tool"](ctx, llm=tools.get("llm"), **args)
                else:
                    res = {"ok": False, "error": f"unknown tool: {tool}"}
            except Exception as e:
                res = {"ok": False, "error": str(e)}
            results.append(
                {"tool": act.get("tool") if isinstance(act, dict) else None, "result": res}
            )
        # If we created a scene, persist it in state for continuity
        next_state = {**state, "action_results": results}
        if narrative_result is not None:
            next_state["narrative_result"] = narrative_result
        if new_scene_id and not next_state.get("scene_id"):
            next_state["scene_id"] = new_scene_id
        if new_story_id and not next_state.get("story_id"):
            next_state["story_id"] = new_story_id
        if new_universe_id and not next_state.get("universe_id"):
            next_state["universe_id"] = new_universe_id
        if new_tags and not next_state.get("tags"):
            next_state["tags"] = new_tags
        return next_state

    def qa_node(state: dict[str, Any]) -> dict[str, Any]:
        """Answer classification questions tersely via QA agent and finish."""
        msgs = [{"role": "user", "content": state.get("intent", "")}]
        answer = _safe_act("qa", msgs, default="Unsure — insufficient evidence.")
        return {**state, "qa": answer, "draft": answer}

    def narrator(state: dict[str, Any]) -> dict[str, Any]:
        msgs = [{"role": "user", "content": state.get("intent", "")}]
        draft = _safe_act("narrator", msgs, default="")
        return {**state, "draft": draft}

    def continuity_guard(state: dict[str, Any]) -> dict[str, Any]:
        """Use the ContinuityModerator agent to judge drift/incorrectness against tags and scene context.

        Persist minimal structured signal for downstream/recording without regex or local heuristics.
        """
        draft = state.get("draft") or ""
        if not draft.strip():
            return state
        scene_id = state.get("scene_id")
        story_id = state.get("story_id")
        universe_id = state.get("universe_id")
        # Fetch compact ontology context to ground the judgment
        ontology_ctx: dict[str, Any] = {}
        try:
            if scene_id:
                ontology_ctx["system"] = tools["query_tool"](
                    tools["ctx"], "effective_system_for_scene", scene_id=scene_id
                )
                ontology_ctx["participants"] = tools["query_tool"](
                    tools["ctx"], "participants_by_role_for_scene", scene_id=scene_id
                )
                ontology_ctx["relations"] = tools["query_tool"](
                    tools["ctx"], "relations_effective_in_scene", scene_id=scene_id
                )
                ontology_ctx["facts"] = tools["query_tool"](
                    tools["ctx"], "facts_for_scene", scene_id=scene_id
                )[:8]
            elif story_id:
                ontology_ctx["system"] = tools["query_tool"](
                    tools["ctx"], "effective_system_for_story", story_id=story_id
                )
                ontology_ctx["participants"] = tools["query_tool"](
                    tools["ctx"], "participants_by_role_for_story", story_id=story_id
                )
                ontology_ctx["facts"] = tools["query_tool"](
                    tools["ctx"], "facts_for_story", story_id=story_id
                )[:8]
            elif universe_id:
                ontology_ctx["system"] = tools["query_tool"](
                    tools["ctx"], "effective_system_for_universe", universe_id=universe_id
                )
        except Exception:
            pass
        # Optionally produce an agentic summary of ontology context to reduce payload size
        try:
            if ontology_ctx:
                summary = _safe_act(
                    "librarian",
                    [
                        {
                            "role": "user",
                            "content": f"Summarize context in 1-2 lines: {str(ontology_ctx)[:800]}",
                        }
                    ],
                    default=None,
                )
            else:
                summary = None
        except Exception:
            summary = None
        # Provide compact context to the agent
        content = {
            "draft": draft,
            "scene_id": scene_id,
            "ontology": ontology_ctx,
            **({"summary": summary} if summary else {}),
        }
        msg = {"role": "user", "content": json.dumps(content, ensure_ascii=False)}
        verdict = _safe_act("continuity", [msg], default=None)
        if verdict is None:
            return state
        # Accept dict or JSON-like string
        parsed = None
        if isinstance(verdict, dict):
            parsed = verdict
        else:
            try:
                parsed = json.loads(verdict)
            except Exception:
                parsed = {"note": str(verdict)[:200]}
        note = parsed.get("note") if isinstance(parsed, dict) else None
        return {**state, "continuity": parsed, **({"guard_note": note} if note else {})}

    def critic(state: dict[str, Any]) -> dict[str, Any]:
        draft = state.get("draft", "")
        critique = _safe_act("critic", [{"role": "user", "content": draft}], default=None)
        if critique is not None:
            return {**state, "critique": critique}
        return {**state, "critique": {"coherence": 0.9, "length": len(draft)}}

    def archivist(state: dict[str, Any]) -> dict[str, Any]:
        draft = state.get("draft", "")
        summary = _safe_act("archivist", [{"role": "user", "content": draft}], default="")
        return {**state, "summary": summary}

    def resolve_decider(state: dict[str, Any]) -> dict[str, Any]:
        """Ask Resolve agent whether to commit or stage this turn's deltas.

        Builds a minimal deltas preview (like recorder will) and includes steward validations.
        """
        # Build a preview of what we'd record
        preview: dict[str, Any] = {"scene_id": state.get("scene_id")}
        draft = state.get("draft") or ""
        continuity = state.get("continuity")
        if draft.strip():
            fact = {
                "description": draft[:220],
                "occurs_in": state.get("scene_id"),
            }
            if isinstance(continuity, dict):
                fact["continuity"] = {
                    k: continuity.get(k)
                    for k in ("drift", "incorrect", "reasons", "constraints", "note")
                    if continuity.get(k) is not None
                }
            preview["facts"] = [fact]
        validations = state.get("validation") or {}
        val = {
            "ok": bool(validations.get("ok", True)),
            "warnings": validations.get("warnings") or [],
            "errors": validations.get("errors") or [],
        }
        mode = "copilot" if getattr(tools.get("ctx"), "dry_run", True) else "autopilot"
        decision = resolve_commit_tool(
            {
                "llm": tools.get("llm"),
                "deltas": preview,
                "validations": val,
                "mode": mode,
                "hints": {"source": "langgraph"},
            }
        )
        return {**state, "resolve_decision": decision}

    def recorder(state: dict[str, Any]) -> dict[str, Any]:
        # Always record a compact Fact per turn to retain memory of choices
        deltas = {"scene_id": state.get("scene_id")}
        draft = state.get("draft", "")
        continuity = state.get("continuity")
        if draft.strip():
            fact = {
                "description": (draft[:220]),
                "occurs_in": state.get("scene_id"),
            }
            if isinstance(continuity, dict):
                # Persist minimal continuity signal
                fact["continuity"] = {
                    k: continuity.get(k)
                    for k in ("drift", "incorrect", "reasons", "constraints", "note")
                    if continuity.get(k) is not None
                }
            deltas["facts"] = [fact]
        # Respect resolve decision: if agent advises against commit or validations not ok, stage only (dry-run semantics)
        decision = state.get("resolve_decision") or {}
        agent_commit = bool(decision.get("commit")) if isinstance(decision, dict) else False
        validations = state.get("validation") or {}
        validations_ok = bool(validations.get("ok", True))
        # If autopilot, only allow direct commit when agent approves and validations are ok; otherwise force dry-run context
        ctx = tools["ctx"]
        allow_commit = (not getattr(ctx, "dry_run", True)) and agent_commit and validations_ok
        if allow_commit:
            commit = tools["recorder_tool"](ctx, draft=draft, deltas=deltas)
        else:
            # Build a temporary dry-run ctx for staging
            from dataclasses import replace as _replace

            try:
                stage_ctx = _replace(ctx, dry_run=True)
            except Exception:
                stage_ctx = ctx
                try:
                    stage_ctx.dry_run = True
                except Exception:
                    pass
            commit = tools["recorder_tool"](stage_ctx, draft=draft, deltas=deltas)
        return {**state, "commit": commit}

    workflow = StateGraph(State)
    workflow.add_node("intent_router", intent_router)

    # Health gate: optional pre-flight check via Conductor; if any satellite/graph is down, abort early when strict
    def health_gate(state: dict[str, Any]) -> dict[str, Any]:
        strict = _env_flag("MONITOR_AGENTIC_STRICT", "0")
        if not strict:
            return state
        # Run lightweight pings; failures mark engine_down
        ok = True
        try:
            ctx = tools["ctx"]
            # Avoid raising on missing clients; only if present and ping fails we abort
            if getattr(ctx, "query_service", None) is None:
                ok = False
            if hasattr(ctx, "mongo") and ctx.mongo is not None:
                ok = ok and bool(ctx.mongo.ping())
            if hasattr(ctx, "qdrant") and ctx.qdrant is not None:
                ok = ok and bool(ctx.qdrant.ping())
            if hasattr(ctx, "opensearch") and ctx.opensearch is not None:
                ok = ok and bool(ctx.opensearch.ping())
            if hasattr(ctx, "minio") and ctx.minio is not None:
                ok = ok and bool(ctx.minio.ping())
        except Exception:
            ok = False
        return {**state, "engine_ok": ok}

    workflow.add_node("health_gate", health_gate)
    workflow.add_node("director", director)
    workflow.add_node("librarian", librarian)
    workflow.add_node("steward", steward)
    workflow.add_node("planner", planner)
    workflow.add_node("execute_actions", execute_actions)
    workflow.add_node("qa_node", qa_node)
    workflow.add_node("narrator", narrator)
    workflow.add_node("critic", critic)
    workflow.add_node("continuity_guard", continuity_guard)
    workflow.add_node("archivist", archivist)
    workflow.add_node("resolve_decider", resolve_decider)
    workflow.add_node("recorder", recorder)

    workflow.set_entry_point("intent_router")

    # Branch on intent_type: monitor/qa short-circuit vs narrative path
    def _route(state: dict[str, Any]):
        it = (state.get("intent_type") or "").lower()
        if it in ("monitor", "audit_relations"):
            return "execute_actions"  # actions will call queries/recorder as needed
        if it == "qa":
            return "qa_node"
        # In strict mode, run health gate first
        return "health_gate" if _env_flag("MONITOR_AGENTIC_STRICT", "0") else "director"

    workflow.add_conditional_edges(
        "intent_router",
        _route,
        {
            "execute_actions": "execute_actions",
            "qa_node": "qa_node",
            "health_gate": "health_gate",
            "director": "director",
        },
    )

    # After health gate, allow Conductor to abort or continue
    def _post_health(state: dict[str, Any]):
        ok = bool(state.get("engine_ok", True))
        if not ok:
            return "qa_node"  # short-circuit with terse status
        return "director"

    workflow.add_conditional_edges(
        "health_gate", _post_health, {"qa_node": "qa_node", "director": "director"}
    )

    workflow.add_edge("director", "librarian")
    workflow.add_edge("librarian", "steward")

    # Conductor chooses whether to go plan or directly narrate/qa/monitor
    def _post_steward(state: dict[str, Any]):
        snap = {k: state.get(k) for k in ("intent_type", "scene_id", "evidence_summary")}
        choice = _safe_act(
            "conductor",
            [{"role": "user", "content": f"State: {snap}. Options: [planner, narrator, qa_node]"}],
            default="planner",
        )
        ch = (choice or "planner").strip().lower()
        return "planner" if ch not in ("narrator", "qa_node") else ch

    workflow.add_conditional_edges(
        "steward",
        _post_steward,
        {"planner": "planner", "narrator": "narrator", "qa_node": "qa_node"},
    )
    workflow.add_edge("planner", "execute_actions")
    workflow.add_edge("execute_actions", "narrator")

    # Optionally allow conductor to re-route after narrator (e.g., re-plan if drift detected later)
    def _post_narrator(state: dict[str, Any]):
        snap = {k: state.get(k) for k in ("scene_id", "draft")}
        choice = _safe_act(
            "conductor",
            [{"role": "user", "content": f"State: {snap}. Options: [continuity_guard, planner]"}],
            default="continuity_guard",
        )
        ch = (choice or "continuity_guard").strip().lower()
        return "continuity_guard" if ch not in ("planner",) else ch

    workflow.add_conditional_edges(
        "narrator", _post_narrator, {"continuity_guard": "continuity_guard", "planner": "planner"}
    )

    # In strict mode, ensure continuity exists before critic (redundant call is harmless)
    def _needs_continuity(state: dict[str, Any]):
        if _env_flag("MONITOR_AGENTIC_STRICT", "0"):
            return "continuity_guard" if not state.get("continuity") else "critic"
        return "critic"

    workflow.add_conditional_edges(
        "continuity_guard",
        _needs_continuity,
        {"continuity_guard": "continuity_guard", "critic": "critic"},
    )
    workflow.add_edge("critic", "archivist")

    # Copilot checkpoint: allow pause before Recorder based on config/env flag
    pause_before_recorder = bool(
        cfg.get("pause_before_recorder", _env_flag("MONITOR_COPILOT_PAUSE", "0"))
    )

    def should_pause(_: dict[str, Any]) -> bool:
        # Default: do NOT pause in copilot, so tests reach the recorder node unless explicitly paused
        return pause_before_recorder

    workflow.add_edge("archivist", "resolve_decider")
    workflow.add_conditional_edges(
        "resolve_decider",
        should_pause,
        {True: END, False: "recorder"},
    )
    workflow.add_edge("recorder", END)
    workflow.add_edge("qa_node", END)

    compiled = workflow.compile()

    class FlowAdapter:
        def __init__(self, compiled_graph):
            self._compiled = compiled_graph

        def invoke(self, inputs: dict[str, Any]) -> dict[str, Any]:
            try:
                out = self._compiled.invoke(inputs)
                if out is not None:
                    return out
            except Exception:
                pass
            # Fallback: sequential execution to produce a final state dict
            state = dict(inputs)
            for fn in (
                intent_router,
                director,
                librarian,
                steward,
                planner,
                execute_actions,
                narrator,
                continuity_guard,
                critic,
                archivist,
                resolve_decider,
            ):
                state = fn(state)
            if not should_pause(state):
                state = recorder(state)
            return state

    return FlowAdapter(compiled)


def select_engine_backend() -> str:
    """Return 'langgraph' by default; allow explicit override via env."""
    val = os.getenv("MONITOR_ENGINE_BACKEND", "langgraph").lower()
    return "langgraph" if val in ("langgraph", "lg") else "inmemory"
