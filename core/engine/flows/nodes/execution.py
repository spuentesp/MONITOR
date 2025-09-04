"""Action execution node."""

from __future__ import annotations

from typing import Any

from ..state import FlowState


def execute_actions(state: FlowState, tools: dict[str, Any]) -> FlowState:
    """Execute the planned actions using available tools."""
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
                        new_tags = list(args.get("tags") or [])
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
                res = tools["narrative_tool"](ctx, args.get("op"), llm=tools.get("llm"), **payload)
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

        results.append({"tool": act.get("tool") if isinstance(act, dict) else None, "result": res})

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

    return FlowState(next_state)
