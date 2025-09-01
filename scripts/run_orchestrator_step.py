from __future__ import annotations

import typer

from core.engine.orchestrator import run_once

app = typer.Typer()


@app.command()
def step(
    intent: str = typer.Argument(..., help="User intent / high-level goal"),
    scene_id: str = typer.Option(None, help="Scene id to scope retrieval/relations"),
    mode: str = typer.Option("copilot", help="copilot or autopilot"),
):
    out = run_once(intent, scene_id=scene_id, mode=mode)
    typer.echo({k: (v if isinstance(v, dict | list) else str(v)) for k, v in out.items()})


if __name__ == "__main__":
    app()
