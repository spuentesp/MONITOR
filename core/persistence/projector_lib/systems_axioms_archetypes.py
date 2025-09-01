from __future__ import annotations

from typing import Any

from core.domain.axiom import Axiom


class SystemsAxiomsArchetypesMixin:
    def _upsert_archetypes(self, archetypes: list[Any]) -> None:
        rows = []
        for a in archetypes:
            props = {
                "name": a.name,
                "description": getattr(a, "description", None),
                "type": getattr(a, "type", None),
                "attributes": getattr(a, "attributes", {}),
                "relations": getattr(a, "relations", {}),
            }
            props = {k: self._sanitize(v) for k, v in props.items()}
            rows.append({"id": a.id, "props": props})
        self.repo.run(
            """
            UNWIND $rows AS row
            MERGE (n:Archetype {id: row.id})
            SET n += row.props
            """,
            rows=rows,
        )

    def _upsert_systems(self, systems: list[dict[str, Any]]) -> None:
        rows = []
        for s in systems:
            props = {k: self._sanitize(v) for k, v in s.items() if k != "id"}
            rows.append({"id": s.get("id"), "props": props})
        if not rows:
            return
        self.repo.run(
            """
            UNWIND $rows AS row
            MERGE (sys:System {id: row.id})
            SET sys += row.props
            """,
            rows=rows,
        )

    def _upsert_axioms(self, axioms: list[Axiom]) -> None:
        rows = [
            {
                "id": ax.id,
                "props": {
                    "type": ax.type,
                    "semantics": ax.semantics,
                    "description": ax.description,
                    "probability": ax.probability,
                    "min_count": ax.min_count,
                    "enabled": ax.enabled,
                    "refers_to_archetype": ax.refers_to_archetype,
                },
            }
            for ax in axioms
        ]
        if not rows:
            return
        self.repo.run(
            """
            UNWIND $rows AS row
            MERGE (a:Axiom {id: row.id})
            SET a += row.props
            """,
            rows=rows,
        )
        # REFERS_TO archetype, if present
        self.repo.run(
            """
            UNWIND $rows AS row
            WITH row WHERE row.props.refers_to_archetype IS NOT NULL
            MATCH (a:Axiom {id: row.id})
            MATCH (ar:Archetype {id: row.props.refers_to_archetype})
            MERGE (a)-[:REFERS_TO]->(ar)
            """,
            rows=rows,
        )

    def _apply_axiom_to_universes(self, ax: Axiom) -> None:
        if not ax.applies_to:
            return
        self.repo.run(
            """
            UNWIND $ids AS uid
            MATCH (a:Axiom {id:$axid})
            MATCH (u:Universe {id:uid})
            MERGE (a)-[:APPLIES_TO]->(u)
            """,
            ids=ax.applies_to,
            axid=ax.id,
        )
