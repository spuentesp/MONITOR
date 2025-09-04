"""
Legacy compatibility adapter for langgraph_flow.

This module provides backward compatibility while the codebase
transitions to the new modular flow structure.
"""

from __future__ import annotations

from typing import Any

from .flows import build_langgraph_flow as build_flow
from .flows import select_engine_backend


def build_langgraph_flow(tools: Any, config: dict | None = None):
    """
    Legacy compatibility function.

    Redirects to the new modular flow builder.
    """
    return build_flow(tools, config)


# Re-export select_engine_backend for compatibility
__all__ = ["build_langgraph_flow", "select_engine_backend"]
