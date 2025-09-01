import json
from pathlib import Path
from typing import Optional

from core.domain.omniverse import Omniverse
from core.domain.multiverse import Multiverse
from core.domain.universe import Universe
from core.domain.story import Story
from core.domain.entity import ConcreteEntity
from core.domain.sheet import Sheet
from core.domain.event import Event


def build_sample(include_story: bool = True) -> Omniverse:
    # Basic Universe
    universe = Universe(name="Earth-Prime", description="Primary test universe", stories=[], multiverse_id="mv-001",)
    # Optional Story + Entity + Sheet + Event
    if include_story:
        hero = ConcreteEntity(id="ent-hero-001", name="Alex", universe_id=universe.id, type="character")
        sheet = Sheet(id="sheet-hero-001", name="Alex Sheet", type="PC", entity_id=hero.id, story_id=None)
        ev = Event(description="Alex helps a civilian in Downtown", type="narrative", participants=[hero.id], universe_id=universe.id)
        story = Story(title="A Hero's Start", summary="Alex begins their journey.", events=[ev], sheets=[sheet], universe_id=universe.id)
        universe.stories.append(story)

    multiverse = Multiverse(id="mv-001", name="Sample Multiverse", description="Demo multiverse", universes=[universe])
    omni = Omniverse(id="omniverse-001", name="M.O.N.I.T.O.R.", multiverses=[multiverse])
    return omni


def save_omniverse(omni: Omniverse, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    data = omni.model_dump(mode="json")
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    omni = build_sample(include_story=True)
    out_file = Path("/workspaces/MONITOR/memory/sample_omniverse.json")
    save_omniverse(omni, out_file)
    print(f"Wrote sample omniverse to {out_file}")
