from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.persistence.mongo_repos import DocMeta, MongoNarrativeRepository
from core.persistence.mongo_store import MongoStore
from core.persistence.object_store import ObjectStore


@dataclass
class ObjectService:
    objects: ObjectStore
    mongo: MongoStore

    def upload_and_register(
        self,
        *,
        bucket: str,
        key: str,
        data: bytes,
        filename: str,
        content_type: str | None,
        universe_id: str,
        story_id: str | None = None,
        scene_id: str | None = None,
        entity_ids: list[str] | None = None,
        fact_id: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Put object
        self.objects.put_bytes(bucket, key, data, content_type=content_type)
        # Register DocMeta in Mongo
        ns = MongoNarrativeRepository(self.mongo)
        doc = DocMeta(
            universe_id=universe_id,
            story_id=story_id,
            scene_id=scene_id,
            entity_ids=entity_ids,
            fact_id=fact_id,
            filename=filename,
            content_type=content_type,
            size=len(data),
            minio_key=f"{bucket}/{key}",
            meta=meta or {},
        )
        ins = ns.insert_docmeta(doc)
        return {
            "ok": True,
            "doc_id": getattr(ins, "inserted_id", None),
            "minio_key": f"{bucket}/{key}",
        }
