from __future__ import annotations

import pytest

from core.engine.tools import ToolContext, rules_tool


class Q:
    def relation_is_active_in_scene(self, *, a: str, b: str, type: str) -> bool:  # noqa: A003
        return type == "enemy_of" and {a, b} == {"e1", "e2"}

    def participants_by_role_for_scene(self, scene_id: str, *, role: str):  # noqa: A003
        if scene_id == "sc1" and role == "protagonist":
            return [{"id": "e1"}]
        return []

    def entities_in_scene(self, scene_id: str):  # noqa: A003
        return [1, 2, 3, 4] if scene_id == "crowded" else [1]


def test_rules_forbid_relation_violation():
    ctx = ToolContext(query_service=Q())
    res = rules_tool(ctx, "forbid_relation", type="enemy_of", a="e1", b="e2")
    assert res["result"] == "violations" and any("enemy_of" in v for v in res["violations"])  # type: ignore[index]


def test_rules_require_role_ok_and_missing():
    ctx = ToolContext(query_service=Q())
    ok = rules_tool(ctx, "require_role_in_scene", role="protagonist", scene_id="sc1")
    miss = rules_tool(ctx, "require_role_in_scene", role="mentor", scene_id="sc1")
    assert ok["result"] == "ok"
    assert miss["result"] == "violations"


def test_rules_max_participants():
    ctx = ToolContext(query_service=Q())
    ok = rules_tool(ctx, "max_participants", scene_id="sc-ok", limit=4)
    crowded = rules_tool(ctx, "max_participants", scene_id="crowded", limit=3)
    assert ok["result"] == "ok"
    assert crowded["result"] == "violations"
