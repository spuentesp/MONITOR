"""
Fact and relation projection operations.

This module handles projection of facts and their relationships.
"""

from __future__ import annotations

from typing import Any

from core.domain.multiverse import Multiverse


class FactProjector:
    """Handles projection of facts and relations."""
    
    def __init__(self, repo: Any):
        self.repo = repo
    
    def project_facts_and_relations(self, multiverse: Multiverse) -> None:
        """Project facts and their relationships."""
        for universe in multiverse.universes:
            for fact in universe.facts:
                # Upsert Fact
                self.repo.run(
                    """
                    MERGE (f:Fact {id:$id}) 
                    SET f.description=$description, f.universe_id=$universe_id, f.when=$when,
                        f.occurs_in=$occurs_in, f.confidence=$confidence
                    WITH f
                    MATCH (u:Universe {id:$universe_id})
                    MERGE (u)-[:HAS_FACT]->(f)
                    RETURN f
                    """,
                    id=fact.id,
                    description=fact.description,
                    universe_id=universe.id,
                    when=fact.when,
                    occurs_in=fact.occurs_in,
                    confidence=fact.confidence,
                )
                
                # Project Fact Participants
                for participant in fact.participants:
                    self.repo.run(
                        """
                        MATCH (f:Fact {id:$fact_id})
                        MATCH (e:Entity {id:$entity_id})
                        MERGE (f)-[p:PARTICIPANT {role:$role}]->(e)
                        RETURN p
                        """,
                        fact_id=fact.id,
                        entity_id=participant.entity_id,
                        role=participant.role,
                    )
