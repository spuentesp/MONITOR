import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.generation.mock_llm import MockLLM  # noqa: E402
from core.engine import default_narrative_session  # noqa: E402
from core.agents.personificador import character_agent  # noqa: E402
from core.agents.archivista import archivist_agent  # noqa: E402


def test_narrative_session_produces_text():
    sess = default_narrative_session(MockLLM())
    sess.user("We are in a rainy city alley. A shadow moves.")
    out = sess.step()
    assert isinstance(out, str) and len(out) > 0
    assert "What do you do?" in out


def test_character_and_archivist_agents_reply():
    llm = MockLLM()
    char = character_agent(llm, name="Night Hawk")
    arc = archivist_agent(llm)
    msgs = [
        {"role": "user", "content": "The villain advances."},
    ]
    a = char.act(msgs)
    b = arc.act(msgs)
    assert isinstance(a, str) and isinstance(b, str)
    assert "- Summary:" in b
