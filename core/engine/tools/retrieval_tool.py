from __future__ import annotations

from typing import Any

from core.services.retrieval_service import RetrievalService

from . import ToolContext


def retrieval_tool(
    ctx: ToolContext,
    *,
    query: str,
    vector_collection: str,
    text_index: str,
    k: int = 8,
    filter_terms: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Read-only hybrid retrieval (no Resolve gate)."""
    if ctx.qdrant is None or ctx.opensearch is None:
        raise RuntimeError("Qdrant/OpenSearch not configured")
    if ctx.embedder is None:
        raise RuntimeError("No embedder configured in ToolContext")
    svc = RetrievalService(qdrant=ctx.qdrant, opensearch=ctx.opensearch, embedder=ctx.embedder)
    res = svc.search(
        query=query,
        vector_collection=vector_collection,
        text_index=text_index,
        k=k,
        filter_terms=filter_terms,
    )
    return {"ok": True, "results": res}
