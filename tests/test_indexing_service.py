from __future__ import annotations

from typing import Any

from core.services.indexing_service import IndexingService


class FakeQdrant:
    def __init__(self):
        self._calls: list[tuple[str, Any, Any]] = []

    def ensure_collection(self, name: str, vector_size: int, distance: str = "Cosine") -> None:
        self._calls.append(("ensure_collection", name, vector_size))

    def upsert_points(self, points, *, collection: str | None = None) -> None:
        self._calls.append(("upsert", collection, list(points)))


class FakeOpenSearch:
    def __init__(self):
        self._calls: list[tuple[str, Any, Any]] = []

    def ensure_index(self, name: str, *, mappings: dict[str, Any] | None = None) -> None:
        self._calls.append(("ensure_index", name, mappings))

    def index_docs(self, index: str, docs):
        self._calls.append(("index_docs", index, list(docs)))


def test_indexing_service_indexes_both_layers():
    q = FakeQdrant()
    s = FakeOpenSearch()

    def embedder(text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    svc = IndexingService(qdrant=q, opensearch=s, embedder=embedder)
    svc.ensure_targets(vector_collection="vec_docs", vector_size=3, text_index="txt_docs")

    docs = [
        {"doc_id": "d1", "title": "T1", "text": "hello world", "metadata": {"scene_id": "s1"}},
        {"doc_id": "d2", "body": "bye world", "metadata": {"scene_id": "s2"}},
        {"doc_id": "d3"},  # skipped: no text/body
    ]
    out = svc.index_documents(docs, vector_collection="vec_docs", text_index="txt_docs")

    assert out == {"ok": True, "indexed": {"vectors": 2, "texts": 2}}
    # Qdrant upsert called once
    ups = [c for c in q._calls if c[0] == "upsert"]
    assert len(ups) == 1 and ups[0][1] == "vec_docs"
    ids = [p[0] for p in ups[0][2]]
    payloads = [p[2] for p in ups[0][2]]
    assert ids == ["vec:d1", "vec:d2"]
    assert payloads[0]["doc_id"] == "d1"
    # OpenSearch indexed docs
    os_calls = [c for c in s._calls if c[0] == "index_docs"]
    assert len(os_calls) == 1 and os_calls[0][1] == "txt_docs"
    os_docs = os_calls[0][2]
    assert {d["doc_id"] for d in os_docs} == {"d1", "d2"}
