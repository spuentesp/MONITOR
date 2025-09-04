from __future__ import annotations

from typing import Any

from core.persistence.mongo_repos import DocMeta, Memory, NarrativeService, Note, Turn

from . import ToolContext


def narrative_tool(
    ctx: ToolContext,
    op: str,
    *,
    llm: Any | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Resolve-gated NarrativeService operations backed by Mongo.

    Supported ops:
      - insert_turn(text, role, universe_id, story_id?, scene_id?, entity_ids?, fact_id?, meta?)
      - insert_note(text, tags?, universe_id, story_id?, scene_id?, entity_ids?, fact_id?, meta?)
      - insert_memory(text, subject?, confidence?, universe_id, story_id?, scene_id?, entity_ids?, fact_id?, meta?)
      - insert_docmeta(filename, content_type?, size?, minio_key?, universe_id, story_id?, scene_id?, entity_ids?, fact_id?, meta?)
      - list_turns_for_scene(scene_id, limit?)  # read-only
    """
    # Ensure store available
    if ctx.mongo is None:
        raise RuntimeError("Mongo store not configured")
    service = NarrativeService(ctx.mongo)

    # Reads are not gated
    if op == "list_turns_for_scene":
        scene_id = kwargs.get("scene_id")
        limit = int(kwargs.get("limit", 50))
        return {"ok": True, "result": service.list_turns_for_scene(scene_id, limit=limit)}

    # Build a compact preview for Resolve
    preview = {"op": op, "args": {k: ("<bytes>" if k == "data" else v) for k, v in kwargs.items()}}
    mode = "autopilot" if not getattr(ctx, "dry_run", True) else "copilot"
    from core.engine.commit import decide_commit

    decision, allow = decide_commit(llm, preview, {"ok": True}, mode, {"source": "narrative_tool"})
    if not allow:
        return {"ok": True, "mode": "dry_run", "preview": preview, "decision": decision}

    # Perform mutation
    try:
        if op == "insert_turn":
            doc = Turn(
                universe_id=kwargs["universe_id"],
                story_id=kwargs.get("story_id"),
                scene_id=kwargs.get("scene_id"),
                entity_ids=kwargs.get("entity_ids"),
                fact_id=kwargs.get("fact_id"),
                role=kwargs.get("role", "narrator"),
                text=kwargs["text"],
                meta=kwargs.get("meta"),
            )
            ins = service.insert_turn(doc)
        elif op == "insert_note":
            doc = Note(
                universe_id=kwargs["universe_id"],
                story_id=kwargs.get("story_id"),
                scene_id=kwargs.get("scene_id"),
                entity_ids=kwargs.get("entity_ids"),
                fact_id=kwargs.get("fact_id"),
                text=kwargs["text"],
                tags=kwargs.get("tags"),
                meta=kwargs.get("meta"),
            )
            ins = service.insert_note(doc)
        elif op == "insert_memory":
            doc = Memory(
                universe_id=kwargs["universe_id"],
                story_id=kwargs.get("story_id"),
                scene_id=kwargs.get("scene_id"),
                entity_ids=kwargs.get("entity_ids"),
                fact_id=kwargs.get("fact_id"),
                subject=kwargs.get("subject"),
                text=kwargs["text"],
                confidence=kwargs.get("confidence"),
                meta=kwargs.get("meta"),
            )
            ins = service.insert_memory(doc)
        elif op == "insert_docmeta":
            doc = DocMeta(
                universe_id=kwargs["universe_id"],
                story_id=kwargs.get("story_id"),
                scene_id=kwargs.get("scene_id"),
                entity_ids=kwargs.get("entity_ids"),
                fact_id=kwargs.get("fact_id"),
                filename=kwargs["filename"],
                content_type=kwargs.get("content_type"),
                size=kwargs.get("size"),
                minio_key=kwargs.get("minio_key"),
                meta=kwargs.get("meta"),
            )
            ins = service.insert_docmeta(doc)
        else:
            return {"ok": False, "error": f"unknown op: {op}"}
        return {
            "ok": True,
            "mode": "commit",
            "inserted_id": getattr(ins, "inserted_id", None),
            "decision": decision,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "mode": "commit_attempt"}
