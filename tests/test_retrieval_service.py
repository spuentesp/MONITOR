from __future__ import annotations

from core.services.retrieval_service import RetrievalService


class FakeQdrant:
    def __init__(self):
        self.last = None

    def search(self, vector, limit=5, *, collection=None, query_filter=None):
        self.last = {"vector": vector, "collection": collection, "filter": query_filter}
        return [
            {"payload": {"doc_id": "d1", "title": "T1"}, "score": 0.9},
            {"payload": {"doc_id": "d2", "title": "T2"}, "score": 0.7},
        ]


class FakeOpenSearch:
    def __init__(self):
        self.last = None

    def search(self, index, query, *, size=5, filter_terms=None):
        self.last = {"index": index, "query": query, "filter": filter_terms}
        return [
            {"id": "d2", "score": 2.0, "source": {"doc_id": "d2", "title": "T2"}},
            {"id": "d3", "score": 1.5, "source": {"doc_id": "d3", "title": "T3"}},
        ]


def test_retrieval_service_hybrid_and_filters():
    def embedder(q: str):
        return [0.1, 0.2, 0.3]

    q = FakeQdrant()
    s = FakeOpenSearch()
    svc = RetrievalService(qdrant=q, opensearch=s, embedder=embedder)
    res = svc.search(
        query="spider",
        vector_collection="vec_docs",
        text_index="txt_docs",
        k=5,
        filter_terms={"scene_id": "s1"},
    )
    # d2 appears in both; should be on top
    assert res and res[0]["doc_id"] == "d2"
    # ensure both backends received filters
    assert q.last["filter"] == {"scene_id": "s1"}
    assert s.last["filter"] == {"scene_id": "s1"}
