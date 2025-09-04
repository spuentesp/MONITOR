import pytest
pytestmark = pytest.mark.unit

from core.engine.attribute_extractor import distill_entity_attributes


def test_distill_empty():
    assert distill_entity_attributes(None) == {}
    assert distill_entity_attributes("") == {}


def test_distill_basic_kv():
    text = "Type: mutant\nTags: hero, stealthy\nStats: STR: 12, INT: 14"
    out = distill_entity_attributes(text)
    assert out["type"].lower() == "mutant"
    assert "hero" in out["tags"]
    assert "stealthy" in out["tags"] or "stealthy" in out.get("traits", [])
    assert out["stats"]["STR"] == 12
    assert out["stats"]["INT"] == 14


def test_distill_traits_affiliations():
    text = "Traits: brave, cunning; Affiliations: X-Men, Avengers"
    out = distill_entity_attributes(text)
    assert "brave" in out["traits"]
    assert "cunning" in out["traits"]
    assert "X-Men" in out["affiliations"]
    assert "Avengers" in out["affiliations"]
