"""Pydantic models for branches API endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BranchAtSceneReq(BaseModel):
    source_universe_id: str = Field(..., description="Universe to branch from")
    divergence_scene_id: str = Field(
        ..., description="Scene id inside the source universe to branch at"
    )
    new_universe_id: str = Field(
        ..., description="Target universe id (must not exist unless force=true)"
    )
    new_universe_name: str | None = Field(None, description="Optional name for the new universe")
    force: bool = Field(False, description="Allow overwriting existing target universe")
    dry_run: bool = Field(False, description="Return counts only; do not write")


class CloneReq(BaseModel):
    source_universe_id: str
    new_universe_id: str
    new_universe_name: str | None = None
    mode: Literal["full", "subset"] = "full"
    # subset options
    stories: list[str] | None = None
    arcs: list[str] | None = None
    scene_max_index: int | None = None
    include_all_entities: bool = False
    force: bool = False
    dry_run: bool = False


class DiffRes(BaseModel):
    source_universe_id: str
    target_universe_id: str
    counts: dict[str, int]


class TypedList(BaseModel):
    only_in_source: list[str]
    only_in_target: list[str]


class ProvenanceCounts(BaseModel):
    stories: int
    scenes: int
    entities: int
    facts: int


class TypedDiffRes(BaseModel):
    source_universe_id: str
    target_universe_id: str
    stories: TypedList
    scenes: TypedList
    entities: TypedList
    facts: TypedList
    provenance_counts: ProvenanceCounts


class PromoteReq(BaseModel):
    source_universe_id: str = Field(..., description="Branch universe with the changes")
    target_universe_id: str = Field(..., description="Canonical universe to promote changes into")
    strategy: Literal["append_facts", "append_missing", "overwrite"] = "append_facts"
