import json
import pytest
from pathlib import Path

from core.interfaces.cli_interface import init_multiverse

pytestmark = pytest.mark.integration


def test_cli_init_includes_scenes(tmp_path: Path):
    out = tmp_path / "omniverse.json"
    init_multiverse(
        scaffold=Path("scaffolds/sample_init.yaml"),
        out=out,
    )
    assert out.exists(), "Output JSON was not created"

    data = json.loads(out.read_text())
    stories = data["multiverses"][0]["universes"][0]["stories"]
    assert stories, "Expected at least one story"
    story = stories[0]
    assert "scenes" in story, "Story must include scenes list"
    assert len(story["scenes"]) >= 2, "Expected at least two scenes in sample"
    first = story["scenes"][0]
    for key in ("id", "story_id", "sequence_index", "location", "participants"):
        assert key in first
