from __future__ import annotations

import types


def make_fake_qdrant():
    class FakeCollections:
        def __init__(self):
            self.collections = []

    class FakeClient:
        def __init__(self, *_, **__):
            self._collections = FakeCollections()
            self._created = {}
            self._points = {}

        def get_collections(self):
            return self._collections

        def create_collection(self, collection_name, vectors_config):
            self._collections.collections.append(types.SimpleNamespace(name=collection_name))
            self._created[collection_name] = vectors_config

        def upsert(self, collection_name, points):
            self._points.setdefault(collection_name, []).append(points)

        def search(self, collection_name, query_vector, query_filter=None, limit=5):
            return [types.SimpleNamespace(id="p1", score=0.9, payload={"doc_id": "d1"})]

    http_models = types.SimpleNamespace(
        VectorParams=lambda size, distance: {"size": size, "distance": distance},
        Distance=lambda name: name,
        Batch=lambda ids, vectors, payloads: {"ids": ids, "vectors": vectors, "payloads": payloads},
        FieldCondition=lambda key, match: {"key": key, "match": match},
        MatchValue=lambda value: {"value": value},
        Filter=lambda must: {"must": must},
    )

    pkg = types.SimpleNamespace(QdrantClient=FakeClient)
    return pkg, http_models


def test_qdrant_index_minimal(monkeypatch):
    from core.persistence import qdrant_index as qi

    fake_pkg, http_models = make_fake_qdrant()
    # inject qdrant_client and its http.models
    import sys

    sys.modules["qdrant_client"] = fake_pkg
    sys.modules["qdrant_client.http"] = types.SimpleNamespace(models=http_models)

    idx = qi.QdrantIndex(url="http://x:6333").connect()
    assert idx.ping() is True

    idx.ensure_collection("col1", vector_size=3)
    idx.upsert_points([("p1", [0.1, 0.2, 0.3], {"doc_id": "d1"})], collection="col1")
    res = idx.search([0.1, 0.2, 0.3], limit=1, collection="col1")
    assert res and res[0]["payload"]["doc_id"] == "d1"
