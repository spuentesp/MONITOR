import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.engine.context import ContextToken  # noqa: E402


def test_context_token_validates_and_serializes():
    t = ContextToken(omniverse_id="o", multiverse_id="m", universe_id="u")
    j = t.model_dump_json()
    t2 = ContextToken.model_validate_json(j)
    assert t2.universe_id == "u"
