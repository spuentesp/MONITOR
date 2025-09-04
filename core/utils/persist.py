from __future__ import annotations

from typing import Any

from core.utils.constants import MAX_FACT_DESCRIPTION


def truncate_fact_description(text: str, max_len: int = MAX_FACT_DESCRIPTION) -> str:
    """Truncate a fact description with a single ellipsis if over length."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"


def persist_simple_fact_args(draft: str, scene_id: str | None) -> dict[str, Any]:
    """Build a minimal, consistent fact delta payload for staging/commit.
    Truncates description at ~180 chars and includes occurs_in when scene_id is provided.
    """
    desc = truncate_fact_description(draft)
    fact: dict[str, Any] = {"description": desc}
    if scene_id:
        fact["occurs_in"] = scene_id
    return {"facts": [fact], "scene_id": scene_id}
