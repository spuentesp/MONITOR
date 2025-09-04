from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

import types


def make_fake_minio():
    class FakeResp:
        def __init__(self, data: bytes):
            self._data = data

        def read(self):
            return self._data

        def close(self):
            return None

        def release_conn(self):
            return None

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

        def get_object(self, bucket: str, key: str):
            return FakeResp(self._objects[(bucket, key)])

    return types.SimpleNamespace(Minio=FakeMinio)


def test_object_store_minimal(monkeypatch):
    from core.persistence import object_store as osx

    fake_pkg = make_fake_minio()
    import sys

    sys.modules["minio"] = fake_pkg

    s = osx.ObjectStore(endpoint="x:9000").connect()
    assert s.ping() is True
    s.put_bytes("b1", "k1", b"data", content_type="text/plain")
    out = s.get_bytes("b1", "k1")
    assert out == b"data"
