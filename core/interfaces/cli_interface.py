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
from core.persistence.queries import QueryService
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


# --- Queries CLI ---

queries = typer.Typer(help="Query helpers")
app.add_typer(queries, name="q")


def _print_json(obj):
    typer.echo(json.dumps(obj, indent=2, ensure_ascii=False))


@queries.command("entities-in-scene")
def q_entities_in_scene(scene_id: str):
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    _print_json(svc.entities_in_scene(scene_id))
    repo.close()


@queries.command("facts-for-scene")
def q_facts_for_scene(scene_id: str):
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    _print_json(svc.facts_for_scene(scene_id))
    repo.close()


@queries.command("relation-history")
def q_relation_history(entity_a: str, entity_b: str):
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    _print_json(svc.relation_state_history(entity_a, entity_b))
    repo.close()


@queries.command("axioms-for-universe")
def q_axioms_for_universe(universe_id: str):
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    _print_json(svc.axioms_applying_to_universe(universe_id))
    repo.close()

@queries.command("entities-in-arc")
def q_entities_in_arc(arc_id: str):
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    _print_json(svc.entities_in_arc(arc_id))
    repo.close()

@queries.command("facts-for-story")
def q_facts_for_story(story_id: str):
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    _print_json(svc.facts_for_story(story_id))
    repo.close()

@queries.command("system-usage")
def q_system_usage(universe_id: str):
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    _print_json(svc.system_usage_summary(universe_id))
    repo.close()

@queries.command("axioms-in-scene")
def q_axioms_in_scene(scene_id: str):
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    _print_json(svc.axioms_effective_in_scene(scene_id))
    repo.close()

@queries.command("entities-in-universe")
def q_entities_in_universe(universe_id: str):
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    _print_json(svc.entities_in_universe(universe_id))
    repo.close()

@queries.command("entities-in-story-by-role")
def q_entities_in_story_by_role(story_id: str, role: str):
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    _print_json(svc.entities_in_story_by_role(story_id, role))
    repo.close()

@queries.command("entities-in-arc-by-role")
def q_entities_in_arc_by_role(arc_id: str, role: str):
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    _print_json(svc.entities_in_arc_by_role(arc_id, role))
    repo.close()

@queries.command("entities-in-universe-by-role")
def q_entities_in_universe_by_role(universe_id: str, role: str):
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    _print_json(svc.entities_in_universe_by_role(universe_id, role))
    repo.close()

@queries.command("participants-by-role-for-scene")
def q_participants_by_role_for_scene(scene_id: str):
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    _print_json(svc.participants_by_role_for_scene(scene_id))
    repo.close()

@queries.command("participants-by-role-for-story")
def q_participants_by_role_for_story(story_id: str):
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    _print_json(svc.participants_by_role_for_story(story_id))
    repo.close()

@queries.command("next-scene-for-entity")
def q_next_scene_for_entity(story_id: str, entity_id: str, after_sequence_index: int):
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    _print_json(svc.next_scene_for_entity_in_story(story_id, entity_id, after_sequence_index) or {})
    repo.close()

@queries.command("prev-scene-for-entity")
def q_prev_scene_for_entity(story_id: str, entity_id: str, before_sequence_index: int):
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    _print_json(svc.previous_scene_for_entity_in_story(story_id, entity_id, before_sequence_index) or {})
    repo.close()

if __name__ == "__main__":
    app()

