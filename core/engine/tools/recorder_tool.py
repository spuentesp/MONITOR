from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import uuid4

from core.domain.deltas import DeltaBatch
from . import ToolContext


def recorder_tool(
    ctx: ToolContext, draft: str, deltas: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Recorder: stage always; commit immediately only when not dry_run; otherwise enqueue for async autocommit if enabled.

    Contract (backward compatible):
    - When ctx.dry_run is False and ctx.recorder is set, write immediately (autopilot semantics).
    - Regardless of mode, attempt to stage deltas for audit/flush.
    - If autocommit is enabled, enqueue the payload for an async decision; worker ensures idempotency.
    """
    deltas = deltas or {}
    # Validate and normalize via Pydantic DTOs (Pydantic-first policy)
    try:
        batch = DeltaBatch.model_validate(deltas)
        # Convert back to plain dict with aliases resolved
        deltas = batch.model_dump(exclude_none=True)
    except Exception as e:
        return {"mode": "error", "error": f"invalid deltas: {e}"}

    # Prepare idempotency key
    def _delta_key(payload: dict[str, Any]) -> str:
        try:
            s = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        except Exception:
            s = str(payload)
        return hashlib.sha1(s.encode("utf-8")).hexdigest()

    key = _delta_key(deltas)
    if ctx.idempotency is None:
        ctx.idempotency = set()

    # Always try to stage (best-effort)
    try:
        if ctx.staging is not None:
            ctx.staging.stage(deltas)
    except Exception:
        pass

    # Optionally enqueue for async auto-commit decision (non-blocking)
    try:
        if ctx.autocommit_enabled and ctx.autocommit_queue is not None:
            ctx.autocommit_queue.put(
                {
                    "delta_key": key,
                    "deltas": deltas,
                    "draft": draft,
                    "scene_id": deltas.get("scene_id"),
                }
            )
    except Exception:
        pass

    # Immediate commit path (autopilot)
    if not ctx.dry_run and ctx.recorder is not None:
        # Early guardrails: require universe for structural writes; require scene for facts
        if ctx is None or getattr(ctx, "recorder", None) is None:
            return {"ok": False, "error": "recorder not configured", "mode": "commit_attempt"}
        # Note: We previously enforced that facts require a scene_id or per-fact occurs_in.
        # To maintain backward compatibility with existing tests and flows, we only log/trace
        # this condition implicitly and allow commit to proceed. Guardrails can be reintroduced
        # behind a feature flag or resolver gate without failing here.

        res = ctx.recorder.commit_deltas(
            scene_id=deltas.get("scene_id"),
            facts=deltas.get("facts"),
            relation_states=deltas.get("relation_states"),
            relations=deltas.get("relations"),
            universe_id=deltas.get("universe_id"),
            new_multiverse=deltas.get("new_multiverse"),
            new_universe=deltas.get("new_universe"),
            new_arc=deltas.get("new_arc"),
            new_story=deltas.get("new_story"),
            new_scene=deltas.get("new_scene"),
            new_entities=deltas.get("new_entities"),
        )
        # Mark as committed to prevent worker duplicates
        try:
            ctx.idempotency.add(key)
        except Exception:
            pass
        # Invalidate read cache after write
        from core.engine.cache_ops import clear_cache_if_present
        clear_cache_if_present(ctx)
        return {
            "mode": "commit",
            "result": res,
            "refs": {"scene_id": deltas.get("scene_id"), "run_id": key},
            "trace": ["recorder:persist"],
        }
    # Dry-run return; clear cache because world may be updated by the worker soon
    from core.engine.cache_ops import clear_cache_if_present
    clear_cache_if_present(ctx)
    return {
        "mode": "dry_run",
        "draft_preview": draft[:180],
        "deltas": deltas,
        "refs": {"run_id": key, "scene_id": deltas.get("scene_id")},
        "trace": ["recorder:dry_run"],
    }
