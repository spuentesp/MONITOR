import json
from pathlib import Path

from dotenv import load_dotenv
import typer

from core.engine.orchestrator import (
    build_live_tools,
    flush_staging,
    run_once,
)
from core.generation.mock_llm import MockLLM
from core.loaders.yaml_loader import load_omniverse_from_yaml
from core.persistence.neo4j_repo import Neo4jRepo
from core.persistence.queries import QueryService
from core.services.branching.brancher_service import BrancherService
from core.services.projection.projection_service import ProjectionService
from core.utils.merge import deep_merge
from core.utils.persist import persist_simple_fact_args

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


_ARG_YAML_PATH = typer.Argument(..., help="Path to multiverse YAML")
_OPT_ENSURE = typer.Option(True, help="Ensure constraints before projecting")


@app.command("project-from-yaml")
def project_from_yaml(
    path: Path = _ARG_YAML_PATH,
    ensure_constraints: bool = _OPT_ENSURE,
):
    repo = Neo4jRepo().connect()
    projector = ProjectionService(repo)
    projector.project_from_yaml(path, ensure_constraints=ensure_constraints)
    typer.echo(f"Projected YAML into Neo4j: {path}")
    repo.close()


# --- Agents / Orchestrator CLI ---


@app.command("orchestrate-step")
def orchestrate_step(
    intent: str = typer.Argument(..., help="User intent / high-level goal"),
    scene_id: str | None = typer.Option(
        None, "--scene-id", help="Scene id to scope retrieval/relations"
    ),
    mode: str = typer.Option("copilot", "--mode", help="copilot (dry-run) or autopilot (commit)"),
    record_fact: bool = typer.Option(
        False, "--record-fact", help="Also record a simple Fact from the draft"
    ),
):
    """Run a single LangGraph step and print the result as JSON."""
    out = run_once(intent, scene_id=scene_id, mode=mode)
    # Optional: persist a simple Fact (draft summary) to demonstrate Recorder
    if record_fact:
        ctx = build_live_tools(dry_run=(mode != "autopilot"))
    draft = out.get("draft") or intent
    commit = persist_simple_fact_args(draft, scene_id)
    from core.engine.tools import recorder_tool

    persisted = recorder_tool(ctx, draft=draft, deltas=commit)
    out["persisted"] = persisted
    typer.echo(json.dumps(out, indent=2, ensure_ascii=False))


@app.command("agents-chat")
def agents_chat(
    mode: str = typer.Option("copilot", "--mode", help="copilot (dry-run) or autopilot (commit)"),
    scene_id: str | None = typer.Option(
        None, "--scene-id", help="Optional scene id for retrieval context"
    ),
    persist: bool = typer.Option(
        False, "--persist", help="Persist a simple Fact per turn from the draft"
    ),
):
    """Interactive REPL to chat with agents and see plan/draft/commit outputs."""
    ctx = build_live_tools(dry_run=(mode != "autopilot"))
    typer.echo("Agents chat. Type :q to quit.")
    while True:
        try:
            intent = input("> ").strip()
        except EOFError:
            break
        if not intent or intent in (":q", "quit", "exit"):
            break
        out = run_once(intent, scene_id=scene_id, mode=mode, ctx=ctx, llm=MockLLM())
        # Optional: persist a simple Fact (draft summary) each turn
        if persist:
            draft = out.get("draft") or intent
            commit = persist_simple_fact_args(draft, scene_id)
            from core.engine.tools import recorder_tool

            persisted = recorder_tool(ctx, draft=draft, deltas=commit)
            out["persisted"] = persisted
        typer.echo(json.dumps(out, indent=2, ensure_ascii=False))


@app.command("flush-staging")
def cli_flush_staging():
    """Flush staged deltas to the graph (commit) and clear caches."""
    ctx = build_live_tools(dry_run=False)
    res = flush_staging(ctx)
    typer.echo(json.dumps(res, indent=2, ensure_ascii=False))


_ARG_DELTAS = typer.Argument(..., help="Path to a JSON file with proposed deltas")
_OPT_FIXES = typer.Option(None, "--fixes", help="Optional JSON with user-provided fixes")
_OPT_MODE = typer.Option("copilot", "--mode", help="copilot (stage) or autopilot (commit)")
_OPT_COMMIT = typer.Option(False, "--commit", help="When --mode autopilot, actually commit")


@app.command("resolve-deltas")
def resolve_deltas(
    deltas_file: Path = _ARG_DELTAS,
    fixes_file: Path | None = _OPT_FIXES,
    mode: str = _OPT_MODE,
    commit: bool = _OPT_COMMIT,
):
    """Validate deltas, apply optional fixes, and stage or commit based on mode."""
    deltas = json.loads(Path(deltas_file).read_text(encoding="utf-8"))
    fixes = json.loads(Path(fixes_file).read_text(encoding="utf-8")) if fixes_file else None

    merged = deep_merge(deltas, fixes or {})
    will_commit = bool(commit and mode == "autopilot")
    ctx = build_live_tools(dry_run=(not will_commit))
    from core.engine.steward import StewardService

    svc = StewardService(ctx.query_service)
    ok, warns, errs = svc.validate(merged)
    result = {"ok": ok, "warnings": warns, "errors": errs, "deltas": merged}
    from core.engine.tools import recorder_tool

    commit_out = recorder_tool(ctx, draft="", deltas=merged)
    result["commit"] = commit_out
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


_OPT_BEAT = typer.Option(..., "--beat", help="Add a beat/intention; repeat flag to add multiple")
_OPT_SCENE = typer.Option(None, "--scene-id", help="Optional scene id for retrieval context")
_OPT_MODE2 = typer.Option("copilot", "--mode", help="copilot (dry-run) or autopilot (commit)")
_OPT_PERSIST = typer.Option(
    False, "--persist", help="Persist a simple Fact per beat from the draft"
)


@app.command("weave-story")
def weave_story(
    beat: list[str] = _OPT_BEAT,
    scene_id: str | None = _OPT_SCENE,
    mode: str = _OPT_MODE2,
    persist: bool = _OPT_PERSIST,
):
    """Run a multi-step session in one run to demonstrate agents weaving a story."""
    ctx = build_live_tools(dry_run=(mode != "autopilot"))
    steps = []
    full_text = []
    for _idx, b in enumerate(beat, start=1):
        out = run_once(b, scene_id=scene_id, mode=mode, ctx=ctx, llm=MockLLM())
        draft = out.get("draft") or b
        full_text.append(draft)
        if persist:
            commit = persist_simple_fact_args(draft, scene_id)
            from core.engine.tools import recorder_tool

            out["persisted"] = recorder_tool(ctx, draft=draft, deltas=commit)
        steps.append(
            {
                "beat": b,
                "plan": out.get("plan"),
                "draft": draft,
                "summary": out.get("summary"),
                "commit": out.get("commit"),
                "persisted": out.get("persisted"),
            }
        )
    result = {
        "scene_id": scene_id,
        "mode": mode,
        "steps": steps,
        "combined_draft": "\n\n".join(full_text),
    }
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


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
    _print_json(
        svc.previous_scene_for_entity_in_story(story_id, entity_id, before_sequence_index) or {}
    )
    repo.close()


if __name__ == "__main__":
    app()


# --- Branching CLI ---


@app.command("branch-universe")
def branch_universe(
    source_universe_id: str = typer.Argument(..., help="ID of the source Universe to branch"),
    divergence_scene_id: str = typer.Argument(
        ..., help="Scene ID where the branch diverges (inclusive)"
    ),
    new_universe_id: str = typer.Argument(..., help="ID for the new branched Universe"),
    name: str | None = typer.Option(None, "--name", help="Optional name for the new Universe"),
    force: bool = typer.Option(False, "--force", help="Overwrite if target universe exists"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Compute counts only; no writes"),
):
    repo = Neo4jRepo().connect()
    svc = BrancherService(repo)
    out = svc.branch_at_scene(
        source_universe_id, divergence_scene_id, new_universe_id, name, force=force, dry_run=dry_run
    )
    _print_json(out)
    repo.close()


@app.command("clone-universe")
def clone_universe(
    source_universe_id: str = typer.Argument(..., help="ID of the source Universe to clone"),
    new_universe_id: str = typer.Argument(..., help="ID for the new cloned Universe"),
    name: str | None = typer.Option(None, "--name", help="Optional name for the new Universe"),
    force: bool = typer.Option(False, "--force", help="Overwrite if target universe exists"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Compute counts only; no writes"),
):
    repo = Neo4jRepo().connect()
    svc = BrancherService(repo)
    out = svc.clone_full(
        source_universe_id, new_universe_id, name, force=force, dry_run=dry_run
    )
    _print_json(out)
    repo.close()


@app.command("clone-universe-subset")
def clone_universe_subset(
    source_universe_id: str = typer.Argument(..., help="ID of the source Universe"),
    new_universe_id: str = typer.Argument(..., help="ID for the new Universe"),
    name: str | None = typer.Option(None, "--name", help="Optional name for the new Universe"),
    stories: str | None = typer.Option(
        None, "--stories", help="Comma-separated Story IDs to include"
    ),
    arcs: str | None = typer.Option(None, "--arcs", help="Comma-separated Arc IDs to include"),
    scene_max_index: int | None = typer.Option(
        None, "--scene-max-index", help="Max scene sequence_index per story"
    ),
    include_all_entities: bool = typer.Option(
        False,
        "--all-entities",
        help="Include all entities in universe, not only those in included scenes",
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite if target universe exists"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Compute counts only; no writes"),
):
    repo = Neo4jRepo().connect()
    svc = BrancherService(repo)
    story_list = [s.strip() for s in stories.split(",")] if stories else None
    arc_list = [a.strip() for a in arcs.split(",")] if arcs else None
    out = svc.clone_subset(
        source_universe_id,
        new_universe_id,
        name,
        stories=story_list,
        arcs=arc_list,
        scene_max_index=scene_max_index,
        include_all_entities=include_all_entities,
        force=force,
        dry_run=dry_run,
    )
    _print_json(out)
    repo.close()
