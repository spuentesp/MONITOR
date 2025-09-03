from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable


Embedder = Callable[[str], list[float]]


@dataclass
class RetrievalService:
    """Hybrid retrieval combining vector (Qdrant) and BM25 (OpenSearch).

    Returns deduplicated results keyed by doc_id with simple score fusion.
    """

    qdrant: Any
    opensearch: Any
    embedder: Embedder

    def search(
        self,
        *,
        query: str,
        vector_collection: str,
        text_index: str,
        k: int = 8,
        filter_terms: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        v = self.embedder(query)
        v_res = self.qdrant.search(vector=v, limit=k, collection=vector_collection, query_filter=filter_terms)
        t_res = self.opensearch.search(index=text_index, query=query, size=k, filter_terms=filter_terms)

        # Normalize and fuse by doc_id
        scored: dict[str, dict[str, Any]] = {}
        # Vector results
        for r in v_res or []:
            payload = r.get("payload") or {}
            doc_id = payload.get("doc_id")
            if not doc_id:
                continue
            cur = scored.setdefault(doc_id, {"doc_id": doc_id, "title": payload.get("title"), "metadata": payload.get("metadata"), "score_v": 0.0, "score_t": 0.0})
            cur["score_v"] = max(cur.get("score_v", 0.0), float(r.get("score") or 0.0))
        # Text results
        for r in t_res or []:
            src = r.get("source") or {}
            doc_id = src.get("doc_id") or r.get("id")
            if not doc_id:
                continue
            cur = scored.setdefault(doc_id, {"doc_id": doc_id, "title": src.get("title"), "metadata": src.get("metadata"), "score_v": 0.0, "score_t": 0.0})
            cur["score_t"] = max(cur.get("score_t", 0.0), float(r.get("score") or 0.0))

        # Simple linear fusion; prioritize items that appear in both
        out = []
        for doc_id, item in scored.items():
            score = item.get("score_v", 0.0) * 0.6 + item.get("score_t", 0.0) * 0.5
            boost = 0.2 if (item.get("score_v", 0.0) > 0 and item.get("score_t", 0.0) > 0) else 0.0
            out.append({"doc_id": doc_id, "title": item.get("title"), "metadata": item.get("metadata"), "score": score + boost})
        out.sort(key=lambda x: x.get("score", 0), reverse=True)
        return out[:k]
