from __future__ import annotations

import pytest

from core.engine.tools import ToolContext, query_tool


class Q:
    def relations_effective_in_scene(self, scene_id: str):
        return []


def test_query_tool_disallowed_method_raises():
    ctx = ToolContext(query_service=Q())
    with pytest.raises(ValueError):
        query_tool(ctx, "not_allowed")


def test_query_tool_missing_callable_raises():
    class Q2:
        pass

    ctx = ToolContext(query_service=Q2())
    with pytest.raises(AttributeError):
        query_tool(ctx, "relations_effective_in_scene", scene_id="s")
