from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from core.utils.env import env_str


@dataclass
class SearchIndex:
    """Minimal OpenSearch wrapper for BM25 full-text search (optional).

    If opensearch-py isn't installed, connect() raises a clear error.
    """

    url: str | None = None
    user: str | None = None
    password: str | None = None
    client: Any | None = None

    def connect(self) -> SearchIndex:
        if self.client is not None:
            return self
        url = self.url or (env_str("OPENSEARCH_URL") or "http://localhost:9200")
        user = self.user or env_str("OPENSEARCH_USER")
        password = self.password or env_str("OPENSEARCH_PASSWORD")
        try:
            from opensearchpy import OpenSearch
        except Exception as e:  # pragma: no cover - optional dependency
            raise RuntimeError("opensearch-py not installed; cannot use SearchIndex") from e
        auth = (user, password) if user and password else None
        self.client = OpenSearch(hosts=[url], http_auth=auth)
        return self

    def ping(self) -> bool:
        try:
            self.connect()
            assert self.client is not None
            return bool(self.client.ping())
        except Exception:
            return False

    def ensure_index(self, name: str, *, mappings: dict[str, Any] | None = None) -> None:
        self.connect()
        assert self.client is not None
        if not self.client.indices.exists(index=name):
            body = {"settings": {"index": {"number_of_shards": 1, "number_of_replicas": 0}}}
            if mappings:
                body["mappings"] = mappings
            self.client.indices.create(index=name, body=body)

    def index_docs(self, index: str, docs: Iterable[dict[str, Any]]) -> None:
        self.connect()
        assert self.client is not None
        for d in docs:
            _id = d.get("id")
            body = {k: v for k, v in d.items() if k != "id"}
            self.client.index(index=index, id=_id, body=body)

    def search(
        self, index: str, query: str, *, size: int = 5, filter_terms: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        self.connect()
        assert self.client is not None
        must: list[dict[str, Any]] = [{"query_string": {"query": query}}]
        if filter_terms:
            for k, v in filter_terms.items():
                must.append({"term": {k: v}})
        resp = self.client.search(index=index, body={"query": {"bool": {"must": must}}}, size=size)
        hits = resp.get("hits", {}).get("hits", [])
        return [
            {"id": h.get("_id"), "score": h.get("_score"), "source": h.get("_source")} for h in hits
        ]
