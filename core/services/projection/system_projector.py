"""
System projection operations.

This module handles projection of systems, axioms, and archetypes.
"""

from __future__ import annotations

from typing import Any


class SystemProjector:
    """Handles projection of systems, axioms, and archetypes."""

    def __init__(self, repo: Any):
        self.repo = repo

    def project_systems(self, systems: list[dict[str, Any]]) -> None:
        """Project systems from YAML data."""
        for sys in systems:
            self.repo.run(
                "MERGE (sys:System {id:$id}) SET sys.name=$name, sys.description=$desc RETURN sys",
                id=sys["id"],
                name=sys["name"],
                desc=sys.get("description"),
            )

    def project_axioms(self, axioms: list[dict[str, Any]]) -> None:
        """Project axioms for systems."""
        for axiom in axioms:
            self.repo.run(
                """
                MERGE (a:Axiom {id:$id}) 
                SET a.name=$name, a.description=$desc, a.system_id=$system_id
                RETURN a
                """,
                id=axiom["id"],
                name=axiom["name"],
                desc=axiom.get("description"),
                system_id=axiom.get("system_id"),
            )

    def project_archetypes(self, archetypes: list[dict[str, Any]]) -> None:
        """Project character/entity archetypes."""
        for archetype in archetypes:
            self.repo.run(
                """
                MERGE (arch:Archetype {id:$id}) 
                SET arch.name=$name, arch.description=$desc, arch.system_id=$system_id
                RETURN arch
                """,
                id=archetype["id"],
                name=archetype["name"],
                desc=archetype.get("description"),
                system_id=archetype.get("system_id"),
            )
