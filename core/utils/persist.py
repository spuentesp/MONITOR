from __future__ import annotations

from typing import Any


def persist_simple_fact_args(draft: str, scene_id: str | None) -> dict[str, Any]:
    """Build a minimal, consistent fact delta payload for staging/commit.
    Truncates description at ~180 chars and includes occurs_in when scene_id is provided.
    """
    desc = draft[:180] + ("…" if len(draft) > 180 else "")
    fact: dict[str, Any] = {"description": desc}
    if scene_id:
        fact["occurs_in"] = scene_id
    return {"facts": [fact], "scene_id": scene_id}
