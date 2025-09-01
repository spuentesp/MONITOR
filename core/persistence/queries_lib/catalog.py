from __future__ import annotations

from typing import Any


class CatalogQueries:
    def list_multiverses(self) -> list[dict[str, Any]]:
        return self._rows(
            """
            MATCH (m:Multiverse)
            RETURN m.id AS id, m.name AS name
            ORDER BY name, id
            """,
        )

    def list_universes_for_multiverse(self, multiverse_id: str) -> list[dict[str, Any]]:
        return self._rows(
            """
            MATCH (m:Multiverse {id:$mid})-[:HAS_UNIVERSE]->(u:Universe)
            RETURN u.id AS id, u.name AS name
            ORDER BY name, id
            """,
            mid=multiverse_id,
        )
