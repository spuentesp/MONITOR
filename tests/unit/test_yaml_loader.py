from pathlib import Path
import sys

# tests/unit -> repo root
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.loaders.yaml_loader import load_omniverse_from_yaml  # noqa: E402


def test_loader_builds_domain_and_relations_are_navigable():
    path = ROOT / "tests" / "data" / "example_multiverse.yaml"
    omni = load_omniverse_from_yaml(path)

    assert omni.multiverses, "No multiverses loaded"
    mv = omni.multiverses[0]
    assert mv.axioms and mv.archetypes

    # universes
    assert len(mv.universes) >= 2
    u1, u2 = mv.universes[:2]
    for u in (u1, u2):
        # axioms and archetypes present
        assert len(u.axioms) >= 2
        assert len(u.archetypes) >= 2
        # facts and relation states present
        assert len(u.facts) >= 2
        assert len(u.relation_states) >= 1
        # arcs, stories and scenes present and linked
        assert len(u.arcs) >= 2
        assert len(u.stories) >= 4
        for s in u.stories:
            assert s.universe_id == u.id
            assert s.arc_id is not None
            assert len(s.scenes) >= 2
            for sc in s.scenes:
                assert sc.story_id == s.id
                assert isinstance(sc.sequence_index, int) and sc.sequence_index >= 1
