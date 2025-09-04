from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.persistence.brancher import BranchService
from core.persistence.neo4j_repo import Neo4jRepo

router = APIRouter(prefix="/branches", tags=["branches"])


class BranchAtSceneReq(BaseModel):
    source_universe_id: str = Field(..., description="Universe to branch from")
    divergence_scene_id: str = Field(..., description="Scene id inside the source universe to branch at")
    new_universe_id: str = Field(..., description="Target universe id (must not exist unless force=true)")
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


def _svc() -> BranchService:
    repo = Neo4jRepo().connect()
    return BranchService(repo)


@router.post("/branch-at-scene")
def branch_at_scene(req: BranchAtSceneReq) -> dict[str, Any]:
    try:
        svc = _svc()
        res = svc.branch_universe_at_scene(
            source_universe_id=req.source_universe_id,
            divergence_scene_id=req.divergence_scene_id,
            new_universe_id=req.new_universe_id,
            new_universe_name=req.new_universe_name,
            force=req.force,
            dry_run=req.dry_run,
        )
        return {"ok": True, "result": res}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/clone")
def clone_universe(req: CloneReq) -> dict[str, Any]:
    try:
        svc = _svc()
        if req.mode == "full":
            res = svc.clone_universe_full(
                source_universe_id=req.source_universe_id,
                new_universe_id=req.new_universe_id,
                new_universe_name=req.new_universe_name,
                force=req.force,
                dry_run=req.dry_run,
            )
        else:
            res = svc.clone_universe_subset(
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
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(e)) from e


class DiffRes(BaseModel):
    source_universe_id: str
    target_universe_id: str
    counts: dict[str, int]


@router.get("/{source_universe_id}/diff/{target_universe_id}", response_model=DiffRes)
def diff_universes(source_universe_id: str, target_universe_id: str) -> DiffRes:
    """Compute a typed, count-only diff between two universes (shallow but fast).

    Note: A complete typed diff is a follow-up; this returns presence deltas at entity/story/scene/fact levels.
    """
    repo = Neo4jRepo().connect()
    def _count(q: str, **params) -> int:
        rows = repo.run(q, **params)
        return int(rows[0]["c"]) if rows and "c" in rows[0] else 0

    counts = {
        "stories_only_in_source": _count(
            """
            MATCH (:Universe {id:$u1})-[:HAS_STORY]->(st:Story)
            WHERE NOT EXISTS { MATCH (:Universe {id:$u2})-[:HAS_STORY]->(:Story {id:st.id}) }
            RETURN count(DISTINCT st) AS c
            """,
            u1=source_universe_id,
            u2=target_universe_id,
        ),
        "stories_only_in_target": _count(
            """
            MATCH (:Universe {id:$u2})-[:HAS_STORY]->(st:Story)
            WHERE NOT EXISTS { MATCH (:Universe {id:$u1})-[:HAS_STORY]->(:Story {id:st.id}) }
            RETURN count(DISTINCT st) AS c
            """,
            u1=source_universe_id,
            u2=target_universe_id,
        ),
        "entities_only_in_source": _count(
            """
            MATCH (:Universe {id:$u1})<-[:BELONGS_TO]-(e:Entity)
            WHERE NOT EXISTS { MATCH (:Universe {id:$u2})<-[:BELONGS_TO]-(:Entity {id:$u2 + '/' + e.id}) }
            RETURN count(DISTINCT e) AS c
            """,
            u1=source_universe_id,
            u2=target_universe_id,
        ),
        "entities_only_in_target": _count(
            """
            MATCH (:Universe {id:$u2})<-[:BELONGS_TO]-(e:Entity)
            WHERE NOT EXISTS { MATCH (:Universe {id:$u1})<-[:BELONGS_TO]-(:Entity {id:$u1 + '/' + e.id}) }
            RETURN count(DISTINCT e) AS c
            """,
            u1=source_universe_id,
            u2=target_universe_id,
        ),
        "facts_only_in_source": _count(
            """
            MATCH (:Universe {id:$u1})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(:Scene)<-[:OCCURS_IN]-(f:Fact)
            WHERE NOT EXISTS { MATCH (:Universe {id:$u2})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(:Scene)<-[:OCCURS_IN]-(:Fact {id:$u2 + '/' + f.id}) }
            RETURN count(DISTINCT f) AS c
            """,
            u1=source_universe_id,
            u2=target_universe_id,
        ),
        "facts_only_in_target": _count(
            """
            MATCH (:Universe {id:$u2})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(:Scene)<-[:OCCURS_IN]-(f:Fact)
            WHERE NOT EXISTS { MATCH (:Universe {id:$u1})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(:Scene)<-[:OCCURS_IN]-(:Fact {id:$u1 + '/' + f.id}) }
            RETURN count(DISTINCT f) AS c
            """,
            u1=source_universe_id,
            u2=target_universe_id,
        ),
    }
    return DiffRes(source_universe_id=source_universe_id, target_universe_id=target_universe_id, counts=counts)


class PromoteReq(BaseModel):
    source_universe_id: str = Field(..., description="Branch universe with the changes")
    target_universe_id: str = Field(..., description="Canonical universe to promote changes into")
    strategy: Literal["append_facts", "append_missing", "overwrite"] = "append_facts"


@router.post("/promote")
def promote_branch(req: PromoteReq) -> dict[str, Any]:
    """Promote changes from a branch to a target universe.

    MVP strategy: append Facts that don’t exist in target; skip collisions. Overwrite option replaces properties.
    """
    repo = Neo4jRepo().connect()
    try:
        if req.strategy == "append_facts":
            # Create missing Fact nodes in target with OCCURS_IN mapped by matching story/scene ids
            q = (
                """
                MATCH (u2:Universe {id:$target})-[:HAS_STORY]->(st2:Story)-[:HAS_SCENE]->(sc2:Scene)
                WITH collect({story:st2.id, scene:sc2.id}) AS targets
                MATCH (u1:Universe {id:$source})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
                MATCH (f:Fact)-[:OCCURS_IN]->(sc)
                WITH targets, st, sc, f
                WHERE ANY(t IN targets WHERE t.story = st.id AND t.scene = sc.id)
                WITH st, sc, f
                MATCH (st2:Story {id: st.id}), (sc2:Scene {id: sc.id})
                MERGE (f2:Fact {id:f.id})
                ON CREATE SET f2 += f
                MERGE (f2)-[:OCCURS_IN]->(sc2)
                RETURN count(DISTINCT f) AS inserted
                """
            )
            rows = repo.run(q, source=req.source_universe_id, target=req.target_universe_id)
            inserted = int(rows[0]["inserted"]) if rows else 0
            return {"ok": True, "inserted": inserted}
        elif req.strategy == "append_missing":
            # Copy missing stories/scenes/entities/facts by id (namespaced branches are already unique), skip existing
            ops = 0
            ops += int(
                repo.run(
                    """
                    MATCH (:Universe {id:$src})-[:HAS_STORY]->(st:Story)
                    WITH st
                    MATCH (u2:Universe {id:$tgt})
                    MERGE (u2)-[:HAS_STORY]->(st)
                    RETURN count(DISTINCT st) AS c
                    """,
                    src=req.source_universe_id,
                    tgt=req.target_universe_id,
                )[0]["c"]
            )
            return {"ok": True, "ops": ops}
        elif req.strategy == "overwrite":
            # Risky: replace properties for nodes that exist in target by id
            rows = repo.run(
                """
                MATCH (:Universe {id:$src})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(:Scene)<-[:OCCURS_IN]-(f:Fact)
                MATCH (f2:Fact {id:f.id})
                SET f2 = f
                RETURN count(DISTINCT f2) AS updated
                """,
                src=req.source_universe_id,
            )
            updated = int(rows[0]["updated"]) if rows else 0
            return {"ok": True, "updated": updated}
        else:
            raise HTTPException(status_code=400, detail="Unknown strategy")
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(e)) from e
