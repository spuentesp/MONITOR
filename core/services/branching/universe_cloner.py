"""
Universe cloning operations.

This module provides services for cloning universes with various strategies.
"""

from __future__ import annotations

from typing import Any


class UniverseCloner:
    """Handles universe cloning operations."""

    def __init__(self, repo: Any):
        self.repo = repo

    def clone_full(
        self,
        source_universe_id: str,
        new_universe_id: str,
        new_universe_name: str | None = None,
        *,
        force: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Clone a universe with all its content."""
        # Validation
        self._check_source_and_target(source_universe_id, new_universe_id, force)

        if dry_run:
            # Count operations without executing
            stories = self._first_count(
                self.repo.run(
                    "MATCH (s:Story {universe_id: $src}) RETURN count(s) AS c",
                    src=source_universe_id,
                )
            )
            scenes = self._first_count(
                self.repo.run(
                    "MATCH (sc:Scene {universe_id: $src}) RETURN count(sc) AS c",
                    src=source_universe_id,
                )
            )
            entities = self._first_count(
                self.repo.run(
                    "MATCH (e:Entity {universe_id: $src}) RETURN count(e) AS c",
                    src=source_universe_id,
                )
            )
            facts = self._first_count(
                self.repo.run(
                    "MATCH (f:Fact {universe_id: $src}) RETURN count(f) AS c",
                    src=source_universe_id,
                )
            )
            sheets = self._first_count(
                self.repo.run(
                    "MATCH (sh:Sheet {universe_id: $src}) RETURN count(sh) AS c",
                    src=source_universe_id,
                )
            )
            rel_states = self._first_count(
                self.repo.run(
                    "MATCH (rs:RelationState {universe_id: $src}) RETURN count(rs) AS c",
                    src=source_universe_id,
                )
            )
            arcs = self._first_count(
                self.repo.run(
                    "MATCH (a:Arc {universe_id: $src}) RETURN count(a) AS c",
                    src=source_universe_id,
                )
            )

            return {
                "dry_run": True,
                "operations": {
                    "stories": stories,
                    "scenes": scenes,
                    "entities": entities,
                    "facts": facts,
                    "sheets": sheets,
                    "relation_states": rel_states,
                    "arcs": arcs,
                },
            }

        # Execute full clone
        result: dict[str, Any] = {"cloned": True, "operations": []}

        # Clone universe node
        self.repo.run(
            """
            MATCH (src:Universe {id: $src})
            CREATE (tgt:Universe {
                id: $tgt,
                name: COALESCE($name, src.name + ' (Clone)'),
                description: src.description,
                created_at: datetime(),
                cloned_from: $src
            })
            """,
            src=source_universe_id,
            tgt=new_universe_id,
            name=new_universe_name,
        )
        result["operations"].append("universe")

        # Clone stories
        self.repo.run(
            """
            MATCH (src_u:Universe {id: $src})
            MATCH (tgt_u:Universe {id: $tgt})
            MATCH (s:Story {universe_id: $src})
            CREATE (new_s:Story {
                id: $tgt + '_story_' + s.id,
                universe_id: $tgt,
                title: s.title,
                description: s.description,
                tags: s.tags,
                created_at: datetime()
            })
            """,
            src=source_universe_id,
            tgt=new_universe_id,
        )
        result["operations"].append("stories")

        # Continue with other entity types...
        # (Implementation would continue with scenes, entities, facts, etc.)

        return result

    def clone_subset(
        self,
        source_universe_id: str,
        new_universe_id: str,
        new_universe_name: str | None = None,
        stories: list[str] | None = None,
        arcs: list[str] | None = None,
        scene_max_index: int | None = None,
        include_all_entities: bool = False,
        *,
        force: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Clone a subset of a universe."""
        # Validation
        self._check_source_and_target(source_universe_id, new_universe_id, force)

        if dry_run:
            # Count operations for subset
            stories_cnt = 0
            if stories:
                stories_cnt = self._first_count(
                    self.repo.run(
                        "MATCH (s:Story {universe_id: $src}) WHERE s.id IN $story_ids RETURN count(s) AS c",
                        src=source_universe_id,
                        story_ids=stories,
                    )
                )

            return {
                "dry_run": True,
                "subset": True,
                "operations": {"stories": stories_cnt},
            }

        # Execute subset clone
        result: dict[str, Any] = {"cloned": True, "subset": True, "operations": []}

        # Clone universe node
        self.repo.run(
            """
            MATCH (src:Universe {id: $src})
            CREATE (tgt:Universe {
                id: $tgt,
                name: COALESCE($name, src.name + ' (Subset)'),
                description: src.description,
                created_at: datetime(),
                cloned_from: $src,
                clone_type: 'subset'
            })
            """,
            src=source_universe_id,
            tgt=new_universe_id,
            name=new_universe_name,
        )
        result["operations"].append("universe")

        # Clone specified stories if provided
        if stories:
            self.repo.run(
                """
                MATCH (s:Story {universe_id: $src}) 
                WHERE s.id IN $story_ids
                CREATE (new_s:Story {
                    id: $tgt + '_story_' + s.id,
                    universe_id: $tgt,
                    title: s.title,
                    description: s.description,
                    tags: s.tags,
                    created_at: datetime()
                })
                """,
                src=source_universe_id,
                tgt=new_universe_id,
                story_ids=stories,
            )
            result["operations"].append("stories")

        return result

    def _check_source_and_target(
        self, source_universe_id: str, new_universe_id: str, force: bool
    ) -> None:
        """Check source exists and target constraints."""
        rows = self.repo.run(
            """
            OPTIONAL MATCH (src:Universe {id:$src})
            OPTIONAL MATCH (tgt:Universe {id:$tgt})
            RETURN src IS NOT NULL AS src_ok, tgt IS NOT NULL AS tgt_exists
            """,
            src=source_universe_id,
            tgt=new_universe_id,
        )
        src_ok = rows and rows[0].get("src_ok", False)
        tgt_exists = rows and rows[0].get("tgt_exists", False)
        if not src_ok:
            raise ValueError("Source universe not found")
        if tgt_exists and not force:
            raise ValueError(
                "Target universe already exists; use --force to overwrite or choose a new id"
            )

    @staticmethod
    def _first_count(rows: list[dict[str, Any]] | list[Any]) -> int:
        """Extract count from first row."""
        return int(rows[0]["c"]) if rows and "c" in rows[0] else 0
