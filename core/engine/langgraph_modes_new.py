"""DEPRECATED: This module has been split into focused modules.

The original 1003-line file violated Single Responsibility Principle.
Use the new modular structure in core.engine.modes instead.

This file now serves as a backward compatibility layer.
"""

# Re-export the main interface for backward compatibility
from .modes import GraphState, Mode, build_langgraph_modes
from .modes.constants import HELP_TEXT


def get_help_text() -> str:
    """Backward compatibility function."""
    return HELP_TEXT


__all__ = ["build_langgraph_modes", "GraphState", "Mode", "get_help_text"]
