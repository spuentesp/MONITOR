from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any
from core.utils.env import env_str


@dataclass
class MongoStore:
    """Thin MongoDB wrapper for narrative/notes satellites.

    Safe to construct even if pymongo isn't installed; connect() guards imports.
    """

    url: str | None = None
    database: str | None = None
    client: Any | None = None
    db: Any | None = None

    def connect(self) -> MongoStore:
        """Connect lazily using env vars if not provided.

        Env: MONGO_URL, MONGO_DB
        """
        if self.client is not None and self.db is not None:
            return self
        url = self.url or (env_str("MONGO_URL") or "mongodb://localhost:27017")
        database = self.database or (env_str("MONGO_DB") or "monitor")
        try:
            from pymongo import MongoClient  # type: ignore
        except Exception as e:  # pragma: no cover - optional dependency
            raise RuntimeError("pymongo not installed; cannot use MongoStore") from e
        self.client = MongoClient(url, serverSelectionTimeoutMS=1500)
        self.db = self.client[database]
        return self

    def close(self) -> None:
        try:
            if self.client is not None:
                self.client.close()
        finally:
            self.client = None
            self.db = None

    def ping(self) -> bool:
        try:
            self.connect()
            assert self.client is not None
            self.client.admin.command("ping")
            return True
        except Exception:
            return False

    # Minimal helpers (generic)
    def collection(self, name: str):  # Any
        self.connect()
        if self.db is None:  # pragma: no cover - safety
            raise RuntimeError("Mongo database not initialized")
        return self.db[name]

    def insert_document(self, collection: str, doc: dict[str, Any]) -> Any:
        col = self.collection(collection)
        res = col.insert_one(doc)
        return res.inserted_id

    def upsert_document(self, collection: str, key: dict[str, Any], doc: dict[str, Any]) -> Any:
        col = self.collection(collection)
        res = col.update_one(key, {"$set": doc}, upsert=True)
        return getattr(res, "upserted_id", None)

    def find(
        self, collection: str, query: dict[str, Any], *, limit: int = 20
    ) -> list[dict[str, Any]]:
        col = self.collection(collection)
        cur = col.find(query).limit(limit)
        return [x for x in cur]

    def get(self, collection: str, key: dict[str, Any]) -> dict[str, Any] | None:
        col = self.collection(collection)
        return col.find_one(key)
