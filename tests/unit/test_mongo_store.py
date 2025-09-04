from __future__ import annotations

import builtins
import types
from typing import Any


def make_fake_pymongo(doc_store: dict[str, list[dict[str, Any]]]):
    class FakeInsertRes:
        def __init__(self, inserted_id):
            self.inserted_id = inserted_id

    class FakeUpdateRes:
        def __init__(self, upserted_id=None):
            self.upserted_id = upserted_id

    class FakeCollection:
        def __init__(self, name: str):
            self.name = name

        def insert_one(self, doc: dict[str, Any]):
            doc_store.setdefault(self.name, []).append(doc)
            return FakeInsertRes(inserted_id=doc.get("_id") or len(doc_store[self.name]))

        def update_one(self, key: dict[str, Any], payload: dict[str, Any], upsert: bool = False):
            # naive upsert: append if not found
            docs = doc_store.setdefault(self.name, [])
            found = False
            for d in docs:
                if all(d.get(k) == v for k, v in key.items()):
                    d.update(payload.get("$set", {}))
                    found = True
                    break
            if not found and upsert:
                doc = {**key, **payload.get("$set", {})}
                docs.append(doc)
                return FakeUpdateRes(upserted_id=doc.get("_id"))
            return FakeUpdateRes()

        def find(self, query: dict[str, Any]):
            docs = doc_store.get(self.name, [])
            filtered = [d for d in docs if all(d.get(k) == v for k, v in query.items())]

            class _Cursor(list):
                def limit(self, n: int):
                    return _Cursor(self[:n])

            return _Cursor(filtered)

        def find_one(self, key: dict[str, Any]):
            docs = doc_store.get(self.name, [])
            for d in docs:
                if all(d.get(k) == v for k, v in key.items()):
                    return d
            return None

    class FakeDB:
        def __init__(self, name: str):
            self._name = name

        def __getitem__(self, collection: str):
            return FakeCollection(collection)

    class FakeAdmin:
        def command(self, name: str):
            if name != "ping":
                raise ValueError("unsupported")
            return {"ok": 1}

    class FakeClient:
        def __init__(self, *_a, **_k):
            self.admin = FakeAdmin()

        def __getitem__(self, name: str):
            return FakeDB(name)

        def close(self):
            return None

    mod = types.SimpleNamespace(MongoClient=FakeClient)
    return mod


def test_mongo_store_connect_and_ops(monkeypatch):
    from core.persistence import mongo_store as ms

    docs: dict[str, list[dict[str, Any]]] = {}
    fake_mod = make_fake_pymongo(docs)
    monkeypatch.setitem(
        builtins.__dict__["__import__"]("sys").modules, "pymongo", fake_mod
    )  # inject

    store = ms.MongoStore(url="mongodb://x:27017", database="testdb").connect()
    assert store.ping() is True

    # insert
    _id = store.insert_document("notes", {"_id": "d1", "a": 1})
    assert _id == "d1"
    # upsert
    up_id = store.upsert_document("notes", {"_id": "d2"}, {"x": 42})
    assert up_id in ("d2", None)
    # find
    items = store.find("notes", {"a": 1})
    assert len(items) == 1 and items[0]["_id"] == "d1"
    # get
    it = store.get("notes", {"_id": "d2"})
    assert it and it.get("_id") == "d2"
