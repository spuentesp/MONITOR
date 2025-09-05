"""
Narrative content service for MongoDB operations.

Handles storage and retrieval of rich narrative content that complements
the graph ontology.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.domain.narrative_content import (
    CharacterMemory,
    ChatLog,
    ContentType,
    EntityDescription,
    GMNote,
    NarrativeContent,
    NarrativeState,
    SceneAbstract,
)
from core.persistence.mongo_store import MongoStore


class NarrativeContentService:
    """Service for managing narrative content in MongoDB."""

    def __init__(self, mongo_store: MongoStore):
        self.store = mongo_store.connect()
        self.collection = self.store.db.narrative_content

    # ===== Generic Content Operations =====

    def save_content(self, content: NarrativeContent) -> str:
        """Save narrative content to MongoDB."""
        content.updated_at = datetime.utcnow()
        doc = content.model_dump()
        result = self.collection.replace_one({"id": content.id}, doc, upsert=True)
        return content.id

    def get_content(self, content_id: str) -> NarrativeContent | None:
        """Retrieve narrative content by ID."""
        doc = self.collection.find_one({"id": content_id})
        if not doc:
            return None

        # Remove MongoDB's _id field
        doc.pop("_id", None)

        # Dynamically create the right model based on content_type
        content_type = doc.get("content_type")
        model_map = {
            ContentType.DESCRIPTION: EntityDescription,
            ContentType.CHAT_LOG: ChatLog,
            ContentType.SCENE_ABSTRACT: SceneAbstract,
            ContentType.GM_NOTE: GMNote,
            ContentType.NARRATIVE_STATE: NarrativeState,
            ContentType.CHARACTER_MEMORY: CharacterMemory,
        }

        model_class = model_map.get(content_type, NarrativeContent)
        return model_class.model_validate(doc)

    def delete_content(self, content_id: str) -> bool:
        """Delete narrative content."""
        result = self.collection.delete_one({"id": content_id})
        return result.deleted_count > 0

    # ===== Content Type Specific Operations =====

    def get_entity_description(self, entity_id: str) -> EntityDescription | None:
        """Get rich description for an entity."""
        doc = self.collection.find_one(
            {"content_type": ContentType.DESCRIPTION, "entity_id": entity_id}
        )
        if not doc:
            return None
        doc.pop("_id", None)
        return EntityDescription.model_validate(doc)

    def get_scene_chat_logs(self, scene_id: str) -> list[ChatLog]:
        """Get all chat logs for a scene, ordered by creation time."""
        cursor = self.collection.find(
            {"content_type": ContentType.CHAT_LOG, "linked_scene_id": scene_id}
        ).sort("created_at", 1)

        logs = []
        for doc in cursor:
            doc.pop("_id", None)
            logs.append(ChatLog.model_validate(doc))
        return logs

    def get_scene_abstract(self, scene_id: str) -> SceneAbstract | None:
        """Get scene abstract/summary."""
        doc = self.collection.find_one(
            {"content_type": ContentType.SCENE_ABSTRACT, "scene_id": scene_id}
        )
        if not doc:
            return None
        doc.pop("_id", None)
        return SceneAbstract.model_validate(doc)

    def get_active_gm_notes(self, universe_id: str, tags: list[str] | None = None) -> list[GMNote]:
        """Get active GM notes for a universe, optionally filtered by tags."""
        query = {
            "content_type": ContentType.GM_NOTE,
            "universe_id": universe_id,
            "$or": [{"expires_at": {"$exists": False}}, {"expires_at": {"$gt": datetime.utcnow()}}],
        }

        if tags:
            query["tags"] = {"$in": tags}

        cursor = self.collection.find(query).sort("priority", -1).sort("created_at", -1)

        notes = []
        for doc in cursor:
            doc.pop("_id", None)
            notes.append(GMNote.model_validate(doc))
        return notes

    def get_narrative_state(self, universe_id: str) -> NarrativeState | None:
        """Get current narrative state for a universe."""
        doc = self.collection.find_one(
            {"content_type": ContentType.NARRATIVE_STATE, "universe_id": universe_id},
            sort=[("updated_at", -1)],
        )

        if not doc:
            return None
        doc.pop("_id", None)
        return NarrativeState.model_validate(doc)

    def get_character_memory(self, character_id: str) -> CharacterMemory | None:
        """Get character memory and context."""
        doc = self.collection.find_one(
            {"content_type": ContentType.CHARACTER_MEMORY, "character_id": character_id}
        )
        if not doc:
            return None
        doc.pop("_id", None)
        return CharacterMemory.model_validate(doc)

    # ===== Search and Discovery =====

    def search_content(
        self,
        universe_id: str,
        content_types: list[ContentType] | None = None,
        linked_entity_ids: list[str] | None = None,
        text_query: str | None = None,
        limit: int = 50,
    ) -> list[NarrativeContent]:
        """Search narrative content with various filters."""
        query = {"universe_id": universe_id}

        if content_types:
            query["content_type"] = {"$in": content_types}

        if linked_entity_ids:
            query["linked_entity_ids"] = {"$in": linked_entity_ids}

        if text_query:
            query["$text"] = {"$search": text_query}

        cursor = self.collection.find(query).limit(limit).sort("updated_at", -1)

        content_list = []
        for doc in cursor:
            doc.pop("_id", None)
            content_list.append(NarrativeContent.model_validate(doc))
        return content_list

    # ===== Utility Methods =====

    def create_indexes(self) -> None:
        """Create indexes for efficient queries."""
        self.collection.create_index("id", unique=True)
        self.collection.create_index("universe_id")
        self.collection.create_index("content_type")
        self.collection.create_index("linked_scene_id")
        self.collection.create_index("linked_story_id")
        self.collection.create_index("linked_entity_ids")
        self.collection.create_index("entity_id")  # for descriptions
        self.collection.create_index("character_id")  # for memories
        self.collection.create_index("scene_id")  # for abstracts
        self.collection.create_index("tags")  # for GM notes
        self.collection.create_index("created_at")
        self.collection.create_index("updated_at")

        # Text search index
        self.collection.create_index([("title", "text"), ("content", "text")])

    def get_content_stats(self, universe_id: str) -> dict[str, Any]:
        """Get statistics about content in a universe."""
        pipeline = [
            {"$match": {"universe_id": universe_id}},
            {
                "$group": {
                    "_id": "$content_type",
                    "count": {"$sum": 1},
                    "latest": {"$max": "$updated_at"},
                }
            },
        ]

        stats = {}
        for doc in self.collection.aggregate(pipeline):
            stats[doc["_id"]] = {"count": doc["count"], "latest": doc["latest"]}
        return stats
