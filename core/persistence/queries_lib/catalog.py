from __future__ import annotations

from typing import Any

from core.persistence.queries.builders.query_loader import load_query


class CatalogQueries:
    def list_multiverses(self) -> list[dict[str, Any]]:
        return self._rows(
            load_query("list_multiverses"),
        )

    def list_universes_for_multiverse(self, multiverse_id: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("list_universes_for_multiverse"),
            mid=multiverse_id,
        )
