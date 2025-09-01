from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.loaders.yaml_loader import load_omniverse_from_yaml  # noqa: E402


def test_loader_includes_scene_participants_and_system_fields():
    omni = load_omniverse_from_yaml(ROOT / "tests" / "data" / "example_multiverse.yaml")
    mv = omni.multiverses[0]
    u = mv.universes[0]
    # Participants present
    assert any(sc.participants for st in u.stories for sc in st.scenes)
    # System fields propagate (universe/story/entity level may be None in fixture, but sheets have system)
    assert all(sh.system_id for e in u.entities for sh in e.sheets)
