from __future__ import annotations

from typing import Any

from core.services.indexing_service import IndexingService

from . import ToolContext


def indexing_tool(
    ctx: ToolContext,
    *,
    llm: Any | None = None,
    vector_collection: str,
    text_index: str,
    docs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Resolve-gated hybrid indexing (Qdrant + OpenSearch).

    Each doc requires: {doc_id, text|body, title?, metadata?}
    """
    if ctx.qdrant is None or ctx.opensearch is None:
        raise RuntimeError("Qdrant/OpenSearch not configured")
    if ctx.embedder is None:
        raise RuntimeError("No embedder configured in ToolContext")
    svc = IndexingService(qdrant=ctx.qdrant, opensearch=ctx.opensearch, embedder=ctx.embedder)

    # Ensure targets exist (idempotent)
    sample_text = None
    for d in docs:
        t = d.get("text") or d.get("body")
        if t:
            sample_text = t
            break
    if not sample_text:
        return {"ok": False, "error": "no text provided in docs"}
    v = ctx.embedder(sample_text)
    svc.ensure_targets(
        vector_collection=vector_collection, vector_size=len(v), text_index=text_index
    )

    # Resolve gate
    preview = {
        "op": "index_docs",
        "args": {
            "count": len(docs),
            "vector_collection": vector_collection,
            "text_index": text_index,
        },
    }
    mode = "autopilot" if not getattr(ctx, "dry_run", True) else "copilot"
    from core.engine.commit import decide_commit

    decision, allow = decide_commit(llm, preview, {"ok": True}, mode, {"source": "indexing_tool"})
    if not allow:
        return {"ok": True, "mode": "dry_run", "preview": preview, "decision": decision}

    try:
        res = svc.index_documents(docs, vector_collection=vector_collection, text_index=text_index)
        return {"ok": True, "mode": "commit", "result": res, "decision": decision}
    except Exception as e:
        return {"ok": False, "error": str(e), "mode": "commit_attempt"}
