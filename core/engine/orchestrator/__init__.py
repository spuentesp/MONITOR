"""Modular orchestrator package with focused responsibilities.

This package splits the monolithic orchestrator into focused modules following SOLID principles:
- tool_builder.py: Tool context building with caching and auto-commit setup
- mock_query_service.py: Mock query service for dry runs and testing
- autocommit_manager.py: Auto-commit management functions
- orchestration_functions.py: Core orchestration functions (run_once, monitor_reply)
"""

from .autocommit_manager import autocommit_stats, flush_staging
from .orchestration_functions import monitor_reply, run_once
from .tool_builder import build_live_tools

__all__ = [
    "build_live_tools",
    "autocommit_stats",
    "flush_staging",
    "run_once",
    "monitor_reply",
]
