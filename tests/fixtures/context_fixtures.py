"""
Context and configuration fixtures for testing.

Provides simple mock ToolContext for testing.
"""

from __future__ import annotations

from unittest.mock import Mock

from core.engine.tools import ToolContext
from .mock_services import MockQueryService


def mock_tool_context(
    query_service=None,
    recorder=None,
    dry_run: bool = True,
    **kwargs
) -> ToolContext:
    """
    Create a mock ToolContext for testing.
    
    Uses simple mocks for all dependencies.
    """
    return ToolContext(
        query_service=query_service or MockQueryService(),
        recorder=recorder or Mock(),
        dry_run=dry_run,
        read_cache=Mock(),
        staging=Mock(),
        autocommit_enabled=False,
        autocommit_queue=None,
        autocommit_worker=None,
        idempotency=set(),
        qdrant=Mock(),
        embedder=lambda x: [0.0] * 384,
        **kwargs
    )