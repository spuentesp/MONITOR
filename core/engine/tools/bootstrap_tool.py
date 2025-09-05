from __future__ import annotations

from typing import Any
from uuid import uuid4

from .recorder_tool import recorder_tool
from .tool_context import ToolContext


def bootstrap_story_tool(
    ctx: ToolContext,
    *,
    title: str,
    protagonist_name: str | None = None,
    time_label: str | None = None,
    tags: list[str] | None = None,
    universe_id: str | None = None,
) -> dict[str, Any]:
    """Create a new story and initial scene (and optionally universe), then persist via recorder_tool.

    Returns the recorder_tool result and references.
    """
    # Generate stable IDs for returned references so callers can retain context
    u_id = universe_id or f"universe:{uuid4()}"
    st_id = f"story:{uuid4()}"
    sc_id = f"scene:{uuid4()}"
    ent_ids: list[str] = []

    # Build deltas payload with explicit IDs to allow downstream continuity
    new_universe = None if universe_id else {"id": u_id, "name": "Omniverse"}
    new_story = {
        "id": st_id,
        "title": title,
        "universe_id": u_id,
        "tags": (tags or []) if time_label is None else [time_label] + (tags or []),
    }
    new_scene = {"id": sc_id, "title": "Opening Scene", "story_id": st_id, "sequence_index": 1}
    new_entities = None
    if protagonist_name:
        eid = f"entity:{uuid4()}"
        ent_ids.append(eid)
        new_entities = [
            {"id": eid, "name": protagonist_name, "role": "protagonist", "universe_id": u_id}
        ]
    deltas = {
        "new_universe": new_universe,
        "universe_id": u_id,
        "new_story": new_story,
        "new_scene": new_scene,
        "new_entities": new_entities,
    }
    draft = f"Bootstrap: story '{title}' created."  # non-diegetic
    res = recorder_tool(ctx, draft=draft, deltas=deltas)
    # Attach useful references for UI/flow to retain context
    refs = {**(res.get("refs") or {}), "universe_id": u_id, "story_id": st_id, "scene_id": sc_id}
    if ent_ids:
        refs["entity_ids"] = ent_ids
    res["refs"] = refs
    return res
