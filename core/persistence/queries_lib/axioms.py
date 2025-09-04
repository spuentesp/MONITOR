from __future__ import annotations

from typing import Any

from core.persistence.query_files.builders.query_loader import load_query


class AxiomsQueries:
    def axioms_applying_to_universe(self, universe_id: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("axioms_applying_to_universe"),
            uid=universe_id,
        )

    def axioms_effective_in_scene(self, scene_id: str) -> list[dict[str, Any]]:
        return self._rows(
            load_query("axioms_effective_in_scene"),
            sid=scene_id,
        )
