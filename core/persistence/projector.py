from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

try:
    from core.ports.storage import RepoPort
except ImportError:  # pragma: no cover
    RepoPort = Any  # type: ignore

from core.loaders.yaml_loader import load_omniverse_from_yaml
from core.persistence.projector_lib.base import BaseProjector
from core.persistence.projector_lib.entities_sheets import EntitiesSheetsMixin
from core.persistence.projector_lib.facts_relations import FactsRelationsMixin
from core.persistence.projector_lib.stories_scenes import StoriesScenesMixin
from core.persistence.projector_lib.systems_axioms_archetypes import SystemsAxiomsArchetypesMixin
from core.persistence.projector_lib.universe_and_arcs import UniverseAndArcsMixin


class Projector(
    BaseProjector,
    SystemsAxiomsArchetypesMixin,
    UniverseAndArcsMixin,
    StoriesScenesMixin,
    EntitiesSheetsMixin,
    FactsRelationsMixin,
):
    def __init__(self, repo: Any):  # duck-typed to RepoPort | Neo4jRepo when available
        # repo is neo4j_repo in the injected deps
        super().__init__(repo)

    def project_from_yaml(self, yaml_path: Path | str, ensure_constraints: bool = True) -> None:
        if ensure_constraints:
            self.repo.bootstrap_constraints()

        # Load full domain plus raw YAML for top-level constructs not in domain (e.g., systems)
        omni = load_omniverse_from_yaml(yaml_path)
        raw = yaml.safe_load(Path(yaml_path).read_text())

        # Upsert Omniverse
        self.repo.run(
            "MERGE (o:Omniverse {id:$id}) SET o.name=$name RETURN o",
            id=omni.id,
            name=omni.name,
        )

        # Systems: from YAML top-level (loader doesn't attach to Omniverse)
        systems = raw.get("systems", []) or []
        if systems:
            self._upsert_systems(systems)

        for mv in omni.multiverses:
            self._upsert_multiverse(omni.id, mv.id, mv.name, mv.description)
            # Multiverse-level archetypes and axioms
            if getattr(mv, "archetypes", None):
                self._upsert_archetypes(mv.archetypes)
            if getattr(mv, "axioms", None):
                self._upsert_axioms(mv.axioms)
                # applies_to edges at MV level handled at universe level when universes are created

            for u in mv.universes:
                self._upsert_universe(mv.id, u)
