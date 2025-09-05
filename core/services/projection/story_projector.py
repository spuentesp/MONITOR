"""
Story and scene projection operations.

This module handles projection of stories and scenes.
"""

from __future__ import annotations

from typing import Any

from core.domain.multiverse import Multiverse


class StoryProjector:
    """Handles projection of stories and scenes."""

    def __init__(self, repo: Any):
        self.repo = repo

    def project_stories_and_scenes(self, multiverse: Multiverse) -> None:
        """Project stories and their scenes."""
        for universe in multiverse.universes:
            for story in universe.stories:
                # Upsert Story
                self.repo.run(
                    """
                    MERGE (s:Story {id:$id}) 
                    SET s.title=$title, s.summary=$summary, s.universe_id=$universe_id
                    WITH s
                    MATCH (u:Universe {id:$universe_id})
                    MERGE (u)-[:HAS_STORY]->(s)
                    RETURN s
                    """,
                    id=story.id,
                    title=story.title,
                    summary=story.summary,
                    universe_id=universe.id,
                )

                # Upsert Scenes
                for scene in story.scenes:
                    self.repo.run(
                        """
                        MERGE (sc:Scene {id:$id}) 
                        SET sc.story_id=$story_id, sc.universe_id=$universe_id, 
                            sc.sequence_index=$sequence_index, sc.when=$when, sc.location=$location
                        WITH sc
                        MATCH (s:Story {id:$story_id})
                        MERGE (s)-[:HAS_SCENE]->(sc)
                        RETURN sc
                        """,
                        id=scene.id,
                        story_id=story.id,
                        universe_id=universe.id,
                        sequence_index=scene.sequence_index,
                        when=scene.when,
                        location=scene.location,
                    )
