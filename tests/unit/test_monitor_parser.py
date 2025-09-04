from pathlib import Path
import sys
import pytest
pytestmark = pytest.mark.unit

from core.engine.monitor_parser import parse_monitor_intent  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_parse_create_multiverse_with_name_and_id():
    t = '/monitor crear multiverso mv:demo nombre "Demo MV"'
    intent = parse_monitor_intent(t)
    assert intent and intent.action == "create_multiverse"
    assert intent.id == "mv:demo"
    assert intent.name == "Demo MV"


def test_parse_create_universe_with_multiverse():
    t = '@monitor create universe universe:demo name "Demo U" multiverse mv:1'
    intent = parse_monitor_intent(t)
    assert intent and intent.action == "create_universe"
    assert intent.id == "universe:demo"
    assert intent.name == "Demo U"
    assert intent.multiverse_id == "mv:1"


def test_parse_save_fact_with_scene():
    t = "/monitor guardar hecho El héroe encontró una pista scene scene:1"
    intent = parse_monitor_intent(t)
    assert intent and intent.action == "save_fact"
    assert "héroe" in (intent.description or "")
    assert intent.scene_id == "scene:1"
