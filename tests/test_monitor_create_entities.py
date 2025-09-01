from core.engine.monitor_parser import parse_monitor_intent
from core.engine.langgraph_modes import monitor_node
from core.engine.tools import ToolContext


class _Staging:
    def __init__(self):
        self.staged = []

    def stage(self, deltas):
        self.staged.append(deltas)


def test_parse_create_entity_full():
    text = "create character 'Logan' as npc type 'mutant' story st:main scene sc:intro with 'Traits: brave; Affiliations: X-Men'"
    intent = parse_monitor_intent(text)
    assert intent is not None
    assert intent.action == "create_entity"
    assert intent.name == "Logan"
    assert intent.kind == "NPC"
    assert intent.entity_type == "mutant"
    assert intent.story_id == "st:main"
    assert intent.scene_id == "sc:intro"
    assert "brave" in (intent.description or "")


def test_parse_seed_pcs():
    text = "seed pcs 'Rogue', 'Gambit', 'Jubilee'"
    intent = parse_monitor_intent(text)
    assert intent is not None
    assert intent.action == "seed_pcs"
    assert intent.kind == "PC"
    assert intent.names and len(intent.names) == 3


def test_monitor_create_entity_adds_appears_in(monkeypatch):
    # Prepare state and monkeypatch recorder_tool inside monitor module by injecting ctx
    staging = _Staging()
    tools = ToolContext(query_service=object(), recorder=None, dry_run=True, read_cache=None, staging=staging)
    state = {
        "input": "create character 'Logan' as npc type 'mutant' scene sc:intro with 'Traits: brave'",
        "universe_id": "u:demo",
        "scene_id": "sc:intro",
        "messages": [],
        "meta": {},
        "tools": tools,
    }
    # Monkeypatch recorder_tool used by monitor_node via replacing _commit behavior is tricky; instead we rely on returned deltas
    # Call monitor_node (router bypassed)
    out = monitor_node(state)
    assert out.get("last_mode") == "monitor"
    # Validate staged deltas have new_scene with participants
    assert staging.staged, "No deltas staged"
    merged = {}
    for d in staging.staged:
        merged.update(d)
    ns = merged.get("new_scene") or {}
    assert ns.get("id") == "sc:intro"
    parts = ns.get("participants") or []
    assert isinstance(parts, list) and len(parts) == 1
