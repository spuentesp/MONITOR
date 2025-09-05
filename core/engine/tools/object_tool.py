from __future__ import annotations

import base64
from typing import Any

from core.services.object_service import ObjectService

from .tool_context import ToolContext


def object_upload_tool(
    ctx: ToolContext,
    *,
    llm: Any | None = None,
    bucket: str,
    key: str,
    data_b64: str,
    filename: str,
    content_type: str | None,
    universe_id: str,
    story_id: str | None = None,
    scene_id: str | None = None,
    entity_ids: list[str] | None = None,
    fact_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve-gated object upload to MinIO + DocMeta registration in Mongo.

    Data must be base64-encoded to keep the tool JSON-friendly.
    """
    if ctx.minio is None or ctx.mongo is None:
        raise RuntimeError("Object/Mongo stores not configured")

    # Compact preview and resolve
    preview = {
        "op": "object_upload",
        "args": {
            "bucket": bucket,
            "key": key,
            "filename": filename,
            "content_type": content_type,
            "universe_id": universe_id,
        },
    }
    mode = "autopilot" if not getattr(ctx, "dry_run", True) else "copilot"
    from core.engine.commit import decide_commit

    decision, allow = decide_commit(
        llm, preview, {"ok": True}, mode, {"source": "object_upload_tool"}
    )
    if not allow:
        return {"ok": True, "mode": "dry_run", "preview": preview, "decision": decision}

    # Decode and upload
    try:
        data = base64.b64decode(data_b64)
        svc = ObjectService(objects=ctx.minio, mongo=ctx.mongo)
        res = svc.upload_and_register(
            bucket=bucket,
            key=key,
            data=data,
            filename=filename,
            content_type=content_type,
            universe_id=universe_id,
            story_id=story_id,
            scene_id=scene_id,
            entity_ids=entity_ids,
            fact_id=fact_id,
            meta=meta,
        )
        return {"ok": True, "mode": "commit", "result": res, "decision": decision}
    except Exception as e:
        return {"ok": False, "error": str(e), "mode": "commit_attempt"}
