"""
Main projection service using composition pattern.

This module provides the main projector interface that composes
all projection operations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from core.loaders.yaml_loader import load_omniverse_from_yaml
from core.services.projection.entity_projector import EntityProjector
from core.services.projection.fact_projector import FactProjector
from core.services.projection.story_projector import StoryProjector
from core.services.projection.system_projector import SystemProjector
from core.services.projection.universe_projector import UniverseProjector


class ProjectionService:
    """Main projection service that composes all projection operations."""
    
    def __init__(self, repo: Any):
        self.repo = repo
        self.system_projector = SystemProjector(repo)
        self.universe_projector = UniverseProjector(repo)
        self.story_projector = StoryProjector(repo)
        self.entity_projector = EntityProjector(repo)
        self.fact_projector = FactProjector(repo)
    
    def project_from_yaml(self, yaml_path: Path | str, ensure_constraints: bool = True) -> None:
        """Project a complete omniverse from YAML."""
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
            self.system_projector.project_systems(systems)
        
        # Axioms
        axioms = raw.get("axioms", []) or []
        if axioms:
            self.system_projector.project_axioms(axioms)
        
        # Archetypes
        archetypes = raw.get("archetypes", []) or []
        if archetypes:
            self.system_projector.project_archetypes(archetypes)

        # For each Multiverse
        for multiverse in omni.multiverses:
            self.universe_projector.project_multiverse(multiverse)
            self.story_projector.project_stories_and_scenes(multiverse)
            self.entity_projector.project_entities_and_sheets(multiverse)
            self.fact_projector.project_facts_and_relations(multiverse)
