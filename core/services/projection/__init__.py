"""
Projection services package.

This package provides projection operations for converting domain models
to persistence layer representations using a composition-based architecture.
"""

from core.services.projection.entity_projector import EntityProjector
from core.services.projection.fact_projector import FactProjector
from core.services.projection.projection_service import ProjectionService
from core.services.projection.story_projector import StoryProjector
from core.services.projection.system_projector import SystemProjector
from core.services.projection.universe_projector import UniverseProjector

__all__ = [
    "ProjectionService",
    "EntityProjector",
    "FactProjector",
    "StoryProjector",
    "SystemProjector",
    "UniverseProjector",
]
