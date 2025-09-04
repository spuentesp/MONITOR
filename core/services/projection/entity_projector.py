"""
Entity and sheet projection operations.

This module handles projection of entities and their character sheets.
"""

from __future__ import annotations

from typing import Any

from core.domain.multiverse import Multiverse


class EntityProjector:
    """Handles projection of entities and character sheets."""
    
    def __init__(self, repo: Any):
        self.repo = repo
    
    def project_entities_and_sheets(self, multiverse: Multiverse) -> None:
        """Project entities and their character sheets."""
        for universe in multiverse.universes:
            for entity in universe.entities:
                # Upsert Entity
                self.repo.run(
                    """
                    MERGE (e:Entity {id:$id}) 
                    SET e.name=$name, e.universe_id=$universe_id, e.type=$type, 
                        e.archetype_id=$archetype_id, e.system_id=$system_id
                    WITH e
                    MATCH (u:Universe {id:$universe_id})
                    MERGE (u)-[:HAS_ENTITY]->(e)
                    RETURN e
                    """,
                    id=entity.id,
                    name=entity.name,
                    universe_id=universe.id,
                    type=entity.type,
                    archetype_id=entity.archetype_id,
                    system_id=entity.system_id,
                )
                
                # Upsert Character Sheets
                for sheet in entity.sheets:
                    self.repo.run(
                        """
                        MERGE (s:Sheet {id:$id}) 
                        SET s.entity_id=$entity_id, s.system_id=$system_id, 
                            s.attributes=$attributes, s.universe_id=$universe_id
                        WITH s
                        MATCH (e:Entity {id:$entity_id})
                        MERGE (e)-[:HAS_SHEET]->(s)
                        RETURN s
                        """,
                        id=sheet.id,
                        entity_id=entity.id,
                        system_id=sheet.system_id,
                        attributes=sheet.attributes,
                        universe_id=universe.id,
                    )
