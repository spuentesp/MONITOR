from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import os
from typing import Any
from core.utils.env import env_str


@dataclass
class QdrantIndex:
    """Minimal Qdrant wrapper for semantic recall.

    Safe to construct even if qdrant-client isn't installed; connect() guards imports.
    """

    url: str | None = None
    api_key: str | None = None
    collection: str | None = None
    client: Any | None = None

    def connect(self) -> QdrantIndex:
        if self.client is not None:
            return self
        url = self.url or (env_str("QDRANT_URL") or "http://localhost:6333")
        api_key = self.api_key or env_str("QDRANT_API_KEY")
        try:
            from qdrant_client import QdrantClient  # type: ignore
        except Exception as e:  # pragma: no cover - optional dependency
            raise RuntimeError("qdrant-client not installed; cannot use QdrantIndex") from e
        self.client = QdrantClient(url=url, api_key=api_key)
        return self

    def ping(self) -> bool:
        try:
            self.connect()
            assert self.client is not None
            self.client.get_collections()
            return True
        except Exception:
            return False

    def ensure_collection(self, name: str, vector_size: int, distance: str = "Cosine") -> None:
        self.connect()
        assert self.client is not None
        colls = self.client.get_collections().collections
        if not any(c.name == name for c in colls):
            from qdrant_client.http import models as qm  # type: ignore

            self.client.create_collection(
                collection_name=name,
                vectors_config=qm.VectorParams(size=vector_size, distance=qm.Distance(distance)),
            )
        self.collection = name

    def upsert_points(
        self,
        points: Iterable[tuple[str, list[float], dict[str, Any]]],
        *,
        collection: str | None = None,
    ) -> None:
        self.connect()
        assert self.client is not None
        name = collection or self.collection
        if not name:
            raise ValueError("Qdrant collection not set")
        from qdrant_client.http import models as qm  # type: ignore

        ids: list[str] = []
        vecs: list[list[float]] = []
        payloads: list[dict[str, Any]] = []
        for pid, vec, payload in points:
            ids.append(pid)
            vecs.append(vec)
            payloads.append(payload)
        self.client.upsert(
            collection_name=name,
            points=qm.Batch(
                ids=ids,
                vectors=vecs,
                payloads=payloads,
            ),
        )

    def search(
        self,
        vector: list[float],
        limit: int = 5,
        *,
        collection: str | None = None,
        query_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        self.connect()
        assert self.client is not None
        name = collection or self.collection
        if not name:
            raise ValueError("Qdrant collection not set")
        from qdrant_client.http import models as qm  # type: ignore

        filt = None
        if query_filter:
            # Simple exact-match filter builder {field: value}
            must = [
                qm.FieldCondition(key=k, match=qm.MatchValue(value=v))
                for k, v in query_filter.items()
            ]
            filt = qm.Filter(must=must)
        res = self.client.search(
            collection_name=name, query_vector=vector, query_filter=filt, limit=limit
        )
        out: list[dict[str, Any]] = []
        for p in res:
            out.append(
                {
                    "id": getattr(p, "id", None),
                    "score": getattr(p, "score", None),
                    "payload": getattr(p, "payload", None),
                }
            )
        return out
