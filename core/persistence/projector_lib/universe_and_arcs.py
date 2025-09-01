from __future__ import annotations

from core.domain.arc import Arc
from core.domain.universe import Universe


class UniverseAndArcsMixin:
    def _upsert_multiverse(self, omni_id: str, mv_id: str, name: str, description: str | None):
        self.repo.run(
            """
            MERGE (m:Multiverse {id:$id})
            SET m.name=$name, m.description=$description
            WITH m
            MATCH (o:Omniverse {id:$omni_id})
            MERGE (o)-[:HAS]->(m)
            """,
            id=mv_id,
            name=name,
            description=description,
            omni_id=omni_id,
        )

    def _upsert_universe(self, mv_id: str, u: Universe):
        self.repo.run(
            """
            MERGE (u:Universe {id:$id})
            SET u.name=$name, u.description=$description
            WITH u
            MATCH (m:Multiverse {id:$mv_id})
            MERGE (m)-[:HAS_UNIVERSE]->(u)
            """,
            id=u.id,
            name=u.name,
            description=u.description,
            mv_id=mv_id,
        )

        # Universe USES_SYSTEM
        if getattr(u, "system_id", None):
            self.repo.run(
                """
                MATCH (u:Universe {id:$uid})
                MATCH (s:System {id:$sid})
                MERGE (u)-[:USES_SYSTEM]->(s)
                """,
                uid=u.id,
                sid=u.system_id,
            )

        # Axioms & Archetypes at Universe level
        if u.archetypes:
            self._upsert_archetypes(u.archetypes)
        if u.axioms:
            self._upsert_axioms(u.axioms)
            # APPLIES_TO edges
            for ax in u.axioms:
                self._apply_axiom_to_universes(ax)

        # Arcs
        if u.arcs:
            self._upsert_arcs(u.id, u.arcs)

        # Stories & Scenes
        if u.stories:
            self._upsert_stories_and_scenes(u.id, u.stories)

        # Entities & Sheets
        if getattr(u, "entities", None):
            self._upsert_entities_and_sheets(u.id, u.entities)

        # APPEARS_IN from Scene.participants (requires scenes and entities present)
        if u.stories:
            self._upsert_appears_in(u.stories)

        # Facts & Relation States
        if getattr(u, "facts", None):
            self._upsert_facts(u.id, u.facts)
        if getattr(u, "relation_states", None):
            self._upsert_relation_states(u.relation_states)

    def _upsert_arcs(self, universe_id: str, arcs: list[Arc]):
        rows = [
            {
                "id": a.id,
                "props": {
                    "title": a.title,
                    "tags": getattr(a, "tags", []),
                    "ordering_mode": getattr(a, "ordering_mode", None),
                    "universe_id": universe_id,
                    "story_ids": getattr(a, "story_ids", []),
                },
            }
            for a in arcs
        ]
        self.repo.run(
            """
            MATCH (u:Universe {id:$uid})
            UNWIND $rows AS row
            MERGE (a:Arc {id: row.id})
            SET a += row.props
            MERGE (u)-[:HAS_ARC]->(a)
            """,
            uid=universe_id,
            rows=rows,
        )
