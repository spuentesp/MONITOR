import sys
from pathlib import Path
import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.domain.axiom import Axiom  # noqa: E402


def load_data():
    data_path = ROOT / "tests" / "data" / "example_multiverse.yaml"
    return yaml.safe_load(data_path.read_text())


def test_multiverse_axioms_apply_to_all_universes():
    data = load_data()
    mv = data["omniverse"]["multiverses"][0]
    uni_ids = {u["id"] for u in mv["universes"]}
    for ax in mv.get("axioms", []):
        applies = set(ax.get("applies_to", []))
        assert applies.issubset(uni_ids)
        # For this fixture we expect MV axioms apply to all universes
        assert applies == uni_ids


def test_arcs_reference_existing_stories_and_stories_reference_arcs():
    data = load_data()
    mv = data["omniverse"]["multiverses"][0]
    for u in mv["universes"]:
        stories = {s["id"]: s for s in u.get("stories", [])}
        arcs = u.get("arcs", [])
        arc_ids = {a["id"] for a in arcs}
        # Each arc's story_ids must exist in stories
        for a in arcs:
            assert a.get("story_ids"), f"Arc {a['id']} has no stories"
            for sid in a["story_ids"]:
                assert sid in stories, f"Arc {a['id']} references missing story {sid}"
        # Each story must reference an existing arc
        for s in stories.values():
            assert s.get("arc_id") in arc_ids


def test_scene_participants_and_fact_relations_reference_entities_and_scenes():
    data = load_data()
    mv = data["omniverse"]["multiverses"][0]
    for u in mv["universes"]:
        entities = {e["id"] for e in u.get("entities", [])}
        scenes = {sc["id"] for s in u.get("stories", []) for sc in s.get("scenes", [])}
        # Scene participants must exist as entities
        for s in u.get("stories", []):
            for sc in s.get("scenes", []):
                for ent in sc.get("participants", []):
                    assert ent in entities
        # Facts occur in scenes and reference valid entities
        for f in u.get("facts", []):
            assert f.get("occurs_in") in scenes
            for p in f.get("participants", []):
                assert p.get("entity_id") in entities
        # Relation states reference scenes and entities
        for rs in u.get("relation_states", []):
            for k in ("set_in_scene", "changed_in_scene", "ended_in_scene"):
                if rs.get(k):
                    assert rs[k] in scenes
            assert rs.get("entity_a") in entities and rs.get("entity_b") in entities


def test_archetype_and_system_references_are_valid():
    data = load_data()
    mv = data["omniverse"]["multiverses"][0]
    systems = {s["id"] for s in data.get("systems", [])}
    mv_arch = {a["id"] for a in mv.get("archetypes", [])}
    for u in mv["universes"]:
        u_arch = {a["id"] for a in u.get("archetypes", [])}
        all_arch = mv_arch | u_arch
        for e in u.get("entities", []):
            if e.get("archetype_id"):
                assert e["archetype_id"] in all_arch
            for sh in e.get("sheets", []):
                assert sh.get("system_id") in systems


def test_axiom_models_validate_from_yaml():
    data = load_data()
    mv = data["omniverse"]["multiverses"][0]
    # Multiverse axioms
    for ax in mv.get("axioms", []):
        m = Axiom(**ax)
        assert m.id == ax["id"] and m.enabled is True
    # Universe axioms
    for u in mv["universes"]:
        for ax in u.get("axioms", []):
            m = Axiom(**ax)
            assert m.id == ax["id"]
