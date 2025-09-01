from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.loaders.yaml_loader import load_omniverse_from_yaml  # noqa: E402


def test_entities_have_sheets_attached():
    path = ROOT / "tests" / "data" / "example_multiverse.yaml"
    omni = load_omniverse_from_yaml(path)
    mv = omni.multiverses[0]

    for u in mv.universes:
        # All entities should be loaded into universe
        assert len(u.entities) >= 2
        # At least one character has 2 sheets
        found = False
        for e in u.entities:
            if e.type == "character" and len(e.sheets) >= 2:
                found = True
                # Check minimal sheet fields
                for sh in e.sheets:
                    assert sh.id and sh.name and sh.type
        assert found, "Expected at least one character with 2 sheets"
