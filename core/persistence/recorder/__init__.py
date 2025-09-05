"""Modular recorder package with focused persistence operations.

This package splits the monolithic recorder into focused modules following SOLID principles:
- utils.py: Data sanitization and ID generation utilities
- multiverse_recorder.py: Multiverse and universe operations
- story_recorder.py: Story and arc operations
- entity_recorder.py: Entity operations
- scene_recorder.py: Scene operations with participant management
- fact_recorder.py: Fact operations with evidence/source management
- relation_recorder.py: Relationship operations (states and simple relations)
- recorder_service.py: Main service orchestrating all focused operations
"""

from .recorder_service import RecorderService

__all__ = ["RecorderService"]
