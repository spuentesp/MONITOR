import json

import pytest

pytestmark = pytest.mark.unit
from pathlib import Path
import sys

import yaml

# Ensure project root is importable (tests/unit -> repo root)
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_example_multiverse_yaml_shape():
    data_path = ROOT / "tests" / "data" / "example_multiverse.yaml"
    assert data_path.exists(), "Example YAML not found"

    data = yaml.safe_load(data_path.read_text())
    omni = data["omniverse"]
    assert len(omni["multiverses"]) >= 1
    mv = omni["multiverses"][0]

    # Check multiverse has 2 axioms and 2 archetypes
    assert len(mv.get("axioms", [])) >= 2
    assert len(mv.get("archetypes", [])) >= 2

    # Universes
    universes = mv["universes"]
    assert len(universes) >= 2

    for u in universes:
        # Per-universe: 2 axioms, 2 archetypes, 2 arcs, 4 stories (2 per arc), 2 scenes per story
        assert len(u.get("axioms", [])) >= 2
        assert len(u.get("archetypes", [])) >= 2
        assert len(u.get("arcs", [])) >= 2
        stories = u.get("stories", [])
        assert len(stories) >= 4
        for st in stories:
            scenes = st.get("scenes", [])
            assert len(scenes) >= 2
            for sc in scenes:
                assert len(sc.get("participants", [])) >= 1
            # Axioms 'applies_to' should reference at least this universe id
            u_id = u["id"]
            for ax in u.get("axioms", []):
                applies = ax.get("applies_to", [])
                assert u_id in applies, f"Axiom {ax['id']} should apply to {u_id}"
        # Entities: ensure at least 2
        entities = u.get("entities", [])
        assert len(entities) >= 2
        # Each character should have at least 2 sheets
        for e in entities:
            if e.get("type") == "character":
                sheets = e.get("sheets", [])
                assert len(sheets) >= 2
            # Facts and relation states with scene provenance
            facts = u.get("facts", [])
            assert len(facts) >= 2
            for f in facts:
                assert "occurs_in" in f and f["occurs_in"], (
                    "Fact must reference a scene (occurs_in)"
                )
                assert len(f.get("participants", [])) >= 1
            rels = u.get("relation_states", [])
            assert len(rels) >= 1
            for rs in rels:
                # Must have at least one provenance hook
                assert any(
                    rs.get(k) for k in ("set_in_scene", "changed_in_scene", "ended_in_scene")
                )


def test_example_multiverse_yaml_is_json_serializable(tmp_path: Path):
    data_path = ROOT / "tests" / "data" / "example_multiverse.yaml"
    data = yaml.safe_load(data_path.read_text())
    # round-trip through JSON to ensure types are serializable and keys are strings
    out = tmp_path / "roundtrip.json"
    out.write_text(json.dumps(data))
    assert out.exists()
