"""
Tool context building with centralized configuration management.

Legacy compatibility wrapper around the new ToolContextBuilder.
"""

from __future__ import annotations

from core.config import ToolContextBuilder
from core.engine.context import ToolContext


def build_live_tools(dry_run: bool = True) -> ToolContext:
    """
    Legacy compatibility function for building ToolContext.

    Now uses the centralized configuration system for cleaner,
    more maintainable configuration management.

    Args:
        dry_run: If True, use mock services instead of live connections

    Returns:
        Configured ToolContext ready for agent operations
    """
    builder = ToolContextBuilder()
    return builder.build(dry_run=dry_run)
