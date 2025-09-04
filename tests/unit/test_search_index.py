from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

import types


def make_fake_opensearch():
    class FakeIndices:
        def __init__(self):
            self._exists = set()

        def exists(self, index: str) -> bool:
            return index in self._exists

        def create(self, index: str, body):
            self._exists.add(index)

    class FakeClient:
        def __init__(self, *_, **__):
            self.indices = FakeIndices()
            self._docs = {}

        def ping(self):
            return True

        def index(self, index: str, id: str | None, body: dict):
            self._docs.setdefault(index, {})[id] = body

        def search(self, index: str, body: dict, size: int):
            docs = self._docs.get(index, {})
            hits = [{"_id": k, "_score": 1.0, "_source": v} for k, v in docs.items()]
            return {"hits": {"hits": hits[:size]}}

    return types.SimpleNamespace(OpenSearch=FakeClient)


def test_search_index_minimal(monkeypatch):
    from core.persistence import search_index as si

    fake_pkg = make_fake_opensearch()
    import sys

    sys.modules["opensearchpy"] = fake_pkg

    s = si.SearchIndex(url="http://x:9200").connect()
    assert s.ping() is True
    s.ensure_index("idx1")
    s.index_docs("idx1", [{"id": "a", "text": "hello"}])
    res = s.search("idx1", "hello", size=1)
    assert res and res[0]["id"] == "a" and res[0]["source"]["text"] == "hello"
