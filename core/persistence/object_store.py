from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.utils.env import env_bool, env_str


@dataclass
class ObjectStore:
    """Minimal MinIO wrapper for binary assets.

    Uses env: MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_SECURE (0/1)
    """

    endpoint: str | None = None
    access_key: str | None = None
    secret_key: str | None = None
    secure: bool | None = None
    client: Any | None = None

    def connect(self) -> ObjectStore:
        if self.client is not None:
            return self
        ep = self.endpoint or (env_str("MINIO_ENDPOINT") or "localhost:9000")
        ak = self.access_key or (env_str("MINIO_ACCESS_KEY") or "minioadmin")
        sk = self.secret_key or (env_str("MINIO_SECRET_KEY") or "minioadmin")
        secure = self.secure if self.secure is not None else env_bool("MINIO_SECURE", False)
        try:
            from minio import Minio
        except Exception as e:  # pragma: no cover - required dependency
            raise RuntimeError("minio not installed; cannot use ObjectStore") from e
        self.client = Minio(ep, access_key=ak, secret_key=sk, secure=secure)
        return self

    def ping(self) -> bool:
        try:
            self.connect()
            assert self.client is not None
            # List buckets as a cheap health check
            _ = self.client.list_buckets()
            return True
        except Exception:
            return False

    def ensure_bucket(self, bucket: str) -> None:
        self.connect()
        assert self.client is not None
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    def put_bytes(
        self, bucket: str, key: str, data: bytes, *, content_type: str | None = None
    ) -> None:
        self.ensure_bucket(bucket)
        assert self.client is not None
        from io import BytesIO

        stream = BytesIO(data)
        self.client.put_object(bucket, key, stream, length=len(data), content_type=content_type)

    def get_bytes(self, bucket: str, key: str) -> bytes:
        self.connect()
        assert self.client is not None
        resp = self.client.get_object(bucket, key)
        try:
            return resp.read()
        finally:
            resp.close()
            resp.release_conn()
