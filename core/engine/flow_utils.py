from __future__ import annotations

from typing import Any


def tool_schema() -> list[dict[str, Any]]:
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


def ops_prelude(
    actions: list[dict[str, Any]], *, persona: str = "guardian", verbose: bool = True
) -> str | None:
    if not verbose:
        return None
    msgs: list[str] = []
    for a in actions:
        t = a.get("tool") if isinstance(a, dict) else None
        if t == "bootstrap_universe":
            msgs.append("Creating a new universe: axioms/ontology from prompt; persisting.")
        elif t == "bootstrap_story":
            msgs.append("Creating a new story: linking to universe; computing sequence index.")
        elif t in ("recorder_tool", "recorder"):
            msgs.append("Recording facts/events into the current scene.")
        elif t in ("query_tool", "query"):
            msgs.append("Querying knowledge scoped to current context.")
        elif t in ("rules_tool", "rules"):
            msgs.append("Evaluating rules for continuity and constraints.")
        elif t:
            msgs.append(f"Executing tool: {t}.")
    if not msgs:
        return None
    title = "Monitor, Guardian of Time and Space" if persona == "guardian" else "Monitor"
    return f"{title}: Operations — " + " ".join(f"- {m}" for m in msgs)
