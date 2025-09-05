from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from .mongo_store import MongoStore


class BaseDoc(BaseModel):
    universe_id: str
    story_id: str | None = None
    scene_id: str | None = None
    entity_ids: list[str] | None = None
    fact_id: str | None = None


class Turn(BaseDoc):
    _id: str | None = None
    role: str
    text: str
    meta: dict[str, Any] | None = None


class SceneText(BaseDoc):
    _id: str | None = None
    sequence_index: int
    title: str | None = None
    text: str
    meta: dict[str, Any] | None = None


class Note(BaseDoc):
    _id: str | None = None
    text: str
    tags: list[str] | None = None
    meta: dict[str, Any] | None = None


class Memory(BaseDoc):
    _id: str | None = None
    subject: str | None = None
    text: str
    confidence: float | None = None
    meta: dict[str, Any] | None = None


class DocMeta(BaseDoc):
    _id: str | None = None
    filename: str
    content_type: str | None = None
    size: int | None = None
    minio_key: str | None = None
    meta: dict[str, Any] | None = None


@dataclass
class MongoRepos:
    store: MongoStore

    def turns(self):
        return self.store.collection("turns")

    def scenes(self):
        return self.store.collection("scenes_text")

    def notes(self):
        return self.store.collection("notes")

    def memory(self):
        return self.store.collection("memory")

    def docmeta(self):
        return self.store.collection("docmeta")


@dataclass
class MongoNarrativeRepository:
    """MongoDB repository for narrative document operations."""

    store: MongoStore

    def _ensure_graph_ids(self, doc: BaseDoc):
        if not doc.universe_id:
            raise ValueError("universe_id is required")

    def insert_turn(self, doc: Turn) -> Any:
        self._ensure_graph_ids(doc)
        return MongoRepos(self.store).turns().insert_one(doc.model_dump())

    def insert_note(self, doc: Note) -> Any:
        self._ensure_graph_ids(doc)
        return MongoRepos(self.store).notes().insert_one(doc.model_dump())

    def insert_memory(self, doc: Memory) -> Any:
        self._ensure_graph_ids(doc)
        return MongoRepos(self.store).memory().insert_one(doc.model_dump())

    def insert_docmeta(self, doc: DocMeta) -> Any:
        self._ensure_graph_ids(doc)
        return MongoRepos(self.store).docmeta().insert_one(doc.model_dump())

    def list_turns_for_scene(self, scene_id: str, limit: int = 50) -> list[dict[str, Any]]:
        return list(MongoRepos(self.store).turns().find({"scene_id": scene_id}).limit(limit))
