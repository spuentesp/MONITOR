from __future__ import annotations

import types


def make_fake_minio():
    class FakeMinio:
        def __init__(self, *_a, **_k):
            self._buckets = set()
            self._objects = {}
        def list_buckets(self):
            return list(self._buckets)
        def bucket_exists(self, name: str) -> bool:
            return name in self._buckets
        def make_bucket(self, name: str):
            self._buckets.add(name)
        def put_object(self, bucket: str, key: str, data, length: int, content_type=None):
            self._objects[(bucket, key)] = data.read()
    return types.SimpleNamespace(Minio=FakeMinio)


def make_fake_pymongo_insert_tracker(out_ids: list[str]):
    import types as _types
    class FakeInsertRes:
        def __init__(self, inserted_id):
            self.inserted_id = inserted_id
    class Coll:
        def __init__(self, name):
            self.name = name
        def insert_one(self, doc):
            out_ids.append(doc.get("_id") or "doc1")
            return FakeInsertRes(out_ids[-1])
    class DB:
        def __getitem__(self, name):
            return Coll(name)
    class Client:
        def __init__(self, *_a, **_k):
            self.admin = _types.SimpleNamespace(command=lambda *_a, **_k: {"ok": 1})
        def __getitem__(self, name):
            return DB()
        def close(self):
            return None
    return _types.SimpleNamespace(MongoClient=Client)


def test_object_service_upload_and_register(monkeypatch):
    import sys
    sys.modules["minio"] = make_fake_minio()
    sys.modules["pymongo"] = make_fake_pymongo_insert_tracker([])

    from core.persistence.object_store import ObjectStore
    from core.persistence.mongo_store import MongoStore
    from core.services.object_service import ObjectService

    svc = ObjectService(objects=ObjectStore().connect(), mongo=MongoStore().connect())
    res = svc.upload_and_register(
        bucket="b",
        key="k",
        data=b"abc",
        filename="f.txt",
        content_type="text/plain",
        universe_id="u1",
        story_id="s1",
        scene_id="sc1",
        entity_ids=["e1"],
        fact_id=None,
    )
    assert res["ok"] is True
    assert res["doc_id"] is not None
