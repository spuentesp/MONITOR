"""
Universe and arc projection operations.

This module handles projection of universes and narrative arcs.
"""

from __future__ import annotations

from typing import Any

from core.domain.multiverse import Multiverse


class UniverseProjector:
    """Handles projection of universes and arcs."""

    def __init__(self, repo: Any):
        self.repo = repo

    def project_multiverse(self, multiverse: Multiverse) -> None:
        """Project multiverse and its universes."""
        # Upsert Multiverse
        self.repo.run(
            "MERGE (m:Multiverse {id:$id}) SET m.name=$name, m.description=$desc RETURN m",
            id=multiverse.id,
            name=multiverse.name,
            desc=multiverse.description,
        )

        # Project Multiverse-level Axioms
        for axiom in multiverse.axioms:
            self.repo.run(
                """
                MERGE (a:Axiom {id:$id}) 
                SET a.type=$type, a.semantics=$semantics, a.description=$description,
                    a.multiverse_id=$multiverse_id
                WITH a
                MATCH (m:Multiverse {id:$multiverse_id})
                MERGE (m)-[:HAS_AXIOM]->(a)
                RETURN a
                """,
                id=axiom.id,
                type=axiom.type,
                semantics=axiom.semantics,
                description=axiom.description,
                multiverse_id=multiverse.id,
            )

        # Project Multiverse-level Archetypes
        for archetype in multiverse.archetypes:
            self.repo.run(
                """
                MERGE (arch:Archetype {id:$id}) 
                SET arch.name=$name, arch.description=$description, arch.type=$type,
                    arch.multiverse_id=$multiverse_id
                WITH arch
                MATCH (m:Multiverse {id:$multiverse_id})
                MERGE (m)-[:HAS_ARCHETYPE]->(arch)
                RETURN arch
                """,
                id=archetype.id,
                name=archetype.name,
                description=archetype.description,
                type=archetype.type,
                multiverse_id=multiverse.id,
            )

        # Upsert Universes and their Arcs
        for universe in multiverse.universes:
            self.repo.run(
                """
                MERGE (u:Universe {id:$id}) 
                SET u.name=$name, u.description=$desc, u.multiverse_id=$multiverse_id
                WITH u
                MATCH (m:Multiverse {id:$multiverse_id})
                MERGE (m)-[:HAS_UNIVERSE]->(u)
                RETURN u
                """,
                id=universe.id,
                name=universe.name,
                desc=universe.description,
                multiverse_id=multiverse.id,
            )

            # Project Arcs for this universe
            for arc in universe.arcs:
                self.repo.run(
                    """
                    MERGE (a:Arc {id:$id}) 
                    SET a.title=$title, a.universe_id=$universe_id
                    WITH a
                    MATCH (u:Universe {id:$universe_id})
                    MERGE (u)-[:HAS_ARC]->(a)
                    RETURN a
                    """,
                    id=arc.id,
                    title=arc.title,
                    universe_id=universe.id,
                )

            # Project Axioms for this universe
            for axiom in universe.axioms:
                self.repo.run(
                    """
                    MERGE (a:Axiom {id:$id}) 
                    SET a.type=$type, a.semantics=$semantics, a.description=$description,
                        a.universe_id=$universe_id
                    WITH a
                    MATCH (u:Universe {id:$universe_id})
                    MERGE (u)-[:HAS_AXIOM]->(a)
                    RETURN a
                    """,
                    id=axiom.id,
                    type=axiom.type,
                    semantics=axiom.semantics,
                    description=axiom.description,
                    universe_id=universe.id,
                )

            # Project Archetypes for this universe
            for archetype in universe.archetypes:
                self.repo.run(
                    """
                    MERGE (arch:Archetype {id:$id}) 
                    SET arch.name=$name, arch.description=$description, arch.type=$type,
                        arch.universe_id=$universe_id
                    WITH arch
                    MATCH (u:Universe {id:$universe_id})
                    MERGE (u)-[:HAS_ARCHETYPE]->(arch)
                    RETURN arch
                    """,
                    id=archetype.id,
                    name=archetype.name,
                    description=archetype.description,
                    type=archetype.type,
                    universe_id=universe.id,
                )
