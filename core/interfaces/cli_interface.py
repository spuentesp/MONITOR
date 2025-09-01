from typing import Optional
from pathlib import Path
import json

import typer

from core.domain.omniverse import Omniverse
from core.domain.multiverse import Multiverse
from core.domain.universe import Universe
from core.domain.story import Story
from core.domain.entity import ConcreteEntity
from core.domain.sheet import Sheet
from core.domain.event import Event
from core.domain.scene import Scene
from core.persistence.neo4j_repo import Neo4jRepo
from core.persistence.projector import Projector


app = typer.Typer(help="M.O.N.I.T.O.R. CLI")


def _save_json(data: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


@app.command("init-multiverse")
def init_multiverse(
    name: str = typer.Option("M.O.N.I.T.O.R.", help="Omniverse name"),
    multiverse_name: str = typer.Option("Sample Multiverse", help="Multiverse name"),
    universe_name: str = typer.Option("Earth-Prime", help="Universe name"),
    include_story: bool = typer.Option(True, help="Include a basic story with an entity, sheet and event"),
    out: Path = typer.Option(Path("memory/sample_omniverse.json"), help="Output JSON path"),
):
    """Create an Omniverse with one Multiverse and one Universe and save to JSON."""
    universe = Universe(name=universe_name, description="Primary test universe")
    if include_story:
        hero = ConcreteEntity(id="ent-hero-001", name="Alex", universe_id=universe.id, type="character")
        sheet = Sheet(id="sheet-hero-001", name="Alex Sheet", type="PC", entity_id=hero.id)
        story = Story(title="A Hero's Start", summary="Alex begins their journey.", universe_id=universe.id)
        # Event tied to this story
        ev = Event(description="Alex helps a civilian in Downtown", type="narrative", participants=[hero.id], universe_id=universe.id, story_id=story.id, order=1)
        story.events.append(ev)
        # Scenes with ordering and participants
        scene1 = Scene(story_id=story.id, sequence_index=1, when="2025-01-01T10:00:00Z", time_span={"started_at": "2025-01-01T10:00:00Z", "ended_at": "2025-01-01T10:20:00Z"}, recorded_at="Session-1", location="Downtown", participants=[hero.id])
        scene2 = Scene(story_id=story.id, sequence_index=2, when="2025-01-01T22:00:00Z", time_span={"started_at": "2025-01-01T22:00:00Z", "ended_at": "2025-01-01T23:00:00Z"}, recorded_at="Session-1", location="Rooftop", participants=[hero.id])
        story.scenes.extend([scene1, scene2])
        # Attach sheet to story for convenience
        story.sheets.append(sheet)
        universe.stories.append(story)

    multiverse = Multiverse(id="mv-001", name=multiverse_name, description="Demo multiverse", universes=[universe])
    omni = Omniverse(id="omniverse-001", name=name, multiverses=[multiverse])

    _save_json(omni.model_dump(mode="json"), out)
    typer.echo(f"Wrote omniverse JSON to {out}")


"""CLI entry point defined at bottom after all commands are registered."""


@app.command("neo4j-bootstrap")
def neo4j_bootstrap():
    repo = Neo4jRepo().connect()
    ok = repo.ping()
    typer.echo(f"Neo4j ping: {'OK' if ok else 'FAIL'}")
    if ok:
        repo.bootstrap_constraints()
        typer.echo("Constraints ensured.")
    repo.close()


@app.command("project-from-yaml")
def project_from_yaml(
    path: Path = typer.Argument(..., help="Path to multiverse YAML"),
    ensure_constraints: bool = typer.Option(True, help="Ensure constraints before projecting"),
):
    repo = Neo4jRepo().connect()
    projector = Projector(repo)
    projector.project_from_yaml(path, ensure_constraints=ensure_constraints)
    typer.echo(f"Projected YAML into Neo4j: {path}")
    repo.close()


if __name__ == "__main__":
    app()
