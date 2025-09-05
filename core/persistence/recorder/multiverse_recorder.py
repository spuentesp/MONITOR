"""Multiverse and universe persistence operations."""

from __future__ import annotations

from typing import Any

from .utils import ensure_id


class MultiverseRecorder:
    """Handle multiverse and universe creation and linking."""

    def __init__(self, repo: Any):
        self.repo = repo

    def create_multiverse(self, new_multiverse: dict[str, Any]) -> str:
        """Create or update multiverse with omniverse linking."""
        mv_id = ensure_id("multiverse", new_multiverse.get("id"))
        props = {
            "name": new_multiverse.get("name"),
            "description": new_multiverse.get("description"),
        }
        self.repo.run(
            """
            UNWIND [$row] AS row
            MERGE (m:Multiverse {id: row.id})
            SET m.name = row.props.name,
                m.description = row.props.description
            WITH m, row
            OPTIONAL MATCH (o:Omniverse {id: row.omni})
            FOREACH (_ IN CASE WHEN o IS NULL THEN [] ELSE [1] END | MERGE (o)-[:HAS]->(m))
            """,
            row={"id": mv_id, "props": props, "omni": new_multiverse.get("omniverse_id")},
        )
        return mv_id

    def create_universe(self, new_universe: dict[str, Any]) -> str:
        """Create or update universe with multiverse linking."""
        u_id = ensure_id("universe", new_universe.get("id"))
        props = {
            "name": new_universe.get("name"),
            "description": new_universe.get("description"),
        }
        self.repo.run(
            """
            UNWIND [$row] AS row
            MERGE (u:Universe {id: row.id})
            SET u.name = row.props.name,
                u.description = row.props.description
            WITH u, row
            OPTIONAL MATCH (m:Multiverse {id: row.mv})
            FOREACH (_ IN CASE WHEN m IS NULL THEN [] ELSE [1] END | MERGE (m)-[:HAS_UNIVERSE]->(u))
            """,
            row={"id": u_id, "props": props, "mv": new_universe.get("multiverse_id")},
        )
        return u_id
