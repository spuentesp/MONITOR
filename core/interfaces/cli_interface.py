from typing import Optional
from pathlib import Path
import json
import os

import typer
from dotenv import load_dotenv

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
from core.loaders.yaml_loader import load_omniverse_from_yaml


load_dotenv(override=False)
app = typer.Typer(help="M.O.N.I.T.O.R. CLI")


def _save_json(data: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


@app.command("init-multiverse")
def init_multiverse(
    scaffold: Path,
    out: Path = Path("memory/sample_omniverse.json"),
):
    """Create an Omniverse JSON from a scaffold YAML.
    Example: --scaffold scaffolds/sample_init.yaml --out memory/omniverse.json
    """
    if not scaffold or not Path(scaffold).exists():
        raise typer.BadParameter("Provide --scaffold pointing to a YAML file.")
    omni = load_omniverse_from_yaml(scaffold)
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
