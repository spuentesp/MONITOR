from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

Embedder = Callable[[str], list[float]]


@dataclass
class IndexingService:
    """Indexing facade for hybrid search (vectors + BM25).

    - qdrant: QdrantIndex wrapper (required for vector indexing)
    - opensearch: SearchIndex wrapper (required for BM25 indexing)
    - embedder: function(text) -> vector used to embed text

    Methods avoid importing client SDKs at import-time; adapters handle that.
    """

    qdrant: Any
    opensearch: Any
    embedder: Embedder

    def ensure_targets(self, *, vector_collection: str, vector_size: int, text_index: str) -> None:
        self.qdrant.ensure_collection(vector_collection, vector_size)
        # Minimal mapping for OpenSearch to keep metadata searchable
        mappings = {
            "properties": {
                "title": {"type": "text"},
                "body": {"type": "text"},
                "metadata": {"type": "object", "enabled": True},
                "doc_id": {"type": "keyword"},
            }
        }
        self.opensearch.ensure_index(text_index, mappings=mappings)

    def index_documents(
        self,
        docs: Iterable[dict[str, Any]],
        *,
        vector_collection: str,
        text_index: str,
    ) -> dict[str, Any]:
        """Index docs into both stores.

        Input doc shape (minimal):
        - id (optional): point id; defaults to f"vec:{doc_id}"
        - doc_id: stable identifier to dedupe across modalities
        - title?: str
        - text/body: str
        - metadata?: dict[str, Any]
        """
        q_points: list[tuple[str, list[float], dict[str, Any]]] = []
        os_docs: list[dict[str, Any]] = []
        n = 0
        for d in docs:
            doc_id = d.get("doc_id")
            body = d.get("text") or d.get("body") or ""
            if not doc_id or not body:
                # Skip invalid docs silently; caller can validate
                continue
            title = d.get("title")
            meta = d.get("metadata") or {}
            vec = self.embedder(body)
            pid = d.get("id") or f"vec:{doc_id}"
            payload = {"doc_id": doc_id, "title": title, "metadata": meta}
            q_points.append((pid, vec, payload))
            os_docs.append(
                {
                    "id": doc_id,
                    "doc_id": doc_id,
                    "title": title,
                    "body": body,
                    "metadata": meta,
                }
            )
            n += 1
        if q_points:
            self.qdrant.upsert_points(q_points, collection=vector_collection)
        if os_docs:
            self.opensearch.index_docs(index=text_index, docs=os_docs)
        return {"ok": True, "indexed": {"vectors": len(q_points), "texts": len(os_docs)}}
