"""Branching and cloning endpoints for universe management."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from core.utils.http_exceptions import bad_request_from_exception

from .models import BranchAtSceneReq, CloneReq
from .utils import get_brancher_service

router = APIRouter()


@router.post("/branch-at-scene")
def branch_at_scene(req: BranchAtSceneReq) -> dict[str, Any]:
    """Branch a universe at a specific scene."""
    try:
        svc = get_brancher_service()
        res = svc.branch_at_scene(
            source_universe_id=req.source_universe_id,
            scene_id=req.divergence_scene_id,
            new_universe_id=req.new_universe_id,
            new_universe_name=req.new_universe_name,
            force=req.force,
            dry_run=req.dry_run,
        )
        return {"ok": True, "result": res}
    except Exception as e:
        raise bad_request_from_exception(e) from e


@router.post("/clone")
def clone_universe(req: CloneReq) -> dict[str, Any]:
    """Clone a universe with full or subset options."""
    try:
        svc = get_brancher_service()
        if req.mode == "full":
            res = svc.clone_full(
                source_universe_id=req.source_universe_id,
                new_universe_id=req.new_universe_id,
                new_universe_name=req.new_universe_name,
                force=req.force,
                dry_run=req.dry_run,
            )
        else:
            res = svc.clone_subset(
                source_universe_id=req.source_universe_id,
                new_universe_id=req.new_universe_id,
                new_universe_name=req.new_universe_name,
                stories=req.stories,
                arcs=req.arcs,
                scene_max_index=req.scene_max_index,
                include_all_entities=req.include_all_entities,
                force=req.force,
                dry_run=req.dry_run,
            )
        return {"ok": True, "result": res}
    except Exception as e:
        raise bad_request_from_exception(e) from e
