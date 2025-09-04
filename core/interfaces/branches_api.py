from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.persistence.neo4j_repo import Neo4jRepo
from core.services.branching.brancher_service import BrancherService

router = APIRouter(prefix="/branches", tags=["branches"])


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


def _svc() -> BrancherService:
    repo = Neo4jRepo().connect()
    return BrancherService(repo)


@router.post("/branch-at-scene")
def branch_at_scene(req: BranchAtSceneReq) -> dict[str, Any]:
    try:
        svc = _svc()
        res = svc.branch_at_scene(
            source_universe_id=req.source_universe_id,
            scene_id=req.divergence_scene_id,
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
    return DiffRes(
        source_universe_id=source_universe_id, target_universe_id=target_universe_id, counts=counts
    )


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
    provenance: ProvenanceCounts


@router.get("/{source_universe_id}/diff/{target_universe_id}/typed", response_model=TypedDiffRes)
def diff_universes_typed(source_universe_id: str, target_universe_id: str) -> TypedDiffRes:
    """Return typed presence lists and provenance counts between universes.

    Mapping assumes branch/clone naming: target ids may be namespaced with `$target/` prefix.
    """
    repo = Neo4jRepo().connect()

    # Stories present only in source (target expects namespaced ids)
    st_src = repo.run(
        """
        MATCH (:Universe {id:$u1})-[:HAS_STORY]->(st:Story)
        WHERE NOT EXISTS {
            MATCH (:Universe {id:$u2})-[:HAS_STORY]->(:Story {id: $u2 + '/' + st.id})
        }
        RETURN collect(DISTINCT st.id) AS ids
        """,
        u1=source_universe_id,
        u2=target_universe_id,
    )
    st_tgt = repo.run(
        """
        MATCH (:Universe {id:$u2})-[:HAS_STORY]->(st2:Story)
        WITH st2,
             CASE WHEN st2.id STARTS WITH $u2 + '/' THEN substring(st2.id, size($u2)+1) ELSE st2.id END AS orig
        WHERE NOT EXISTS {
            MATCH (:Universe {id:$u1})-[:HAS_STORY]->(:Story {id: orig})
        }
        RETURN collect(DISTINCT st2.id) AS ids
        """,
        u1=source_universe_id,
        u2=target_universe_id,
    )

    # Scenes (compare by namespaced id on target)
    sc_src = repo.run(
        """
        MATCH (:Universe {id:$u1})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
        WHERE NOT EXISTS {
            MATCH (:Universe {id:$u2})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(:Scene {id: $u2 + '/' + st.id + '/' + sc.id})
        }
        RETURN collect(DISTINCT sc.id) AS ids
        """,
        u1=source_universe_id,
        u2=target_universe_id,
    )
    sc_tgt = repo.run(
        """
        MATCH (:Universe {id:$u2})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(sc2:Scene)
        WITH sc2,
             CASE WHEN sc2.id STARTS WITH $u2 + '/' THEN substring(sc2.id, size($u2)+1) ELSE sc2.id END AS orig
        WHERE NOT EXISTS {
            MATCH (:Universe {id:$u1})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(:Scene {id: orig})
        }
        RETURN collect(DISTINCT sc2.id) AS ids
        """,
        u1=source_universe_id,
        u2=target_universe_id,
    )

    # Entities
    e_src = repo.run(
        """
        MATCH (:Universe {id:$u1})<-[:BELONGS_TO]-(e:Entity)
        WHERE NOT EXISTS {
            MATCH (:Universe {id:$u2})<-[:BELONGS_TO]-(:Entity {id:$u2 + '/' + e.id})
        }
        RETURN collect(DISTINCT e.id) AS ids
        """,
        u1=source_universe_id,
        u2=target_universe_id,
    )
    e_tgt = repo.run(
        """
        MATCH (:Universe {id:$u2})<-[:BELONGS_TO]-(e2:Entity)
        WITH e2,
             CASE WHEN e2.id STARTS WITH $u2 + '/' THEN substring(e2.id, size($u2)+1) ELSE e2.id END AS orig
        WHERE NOT EXISTS {
            MATCH (:Universe {id:$u1})<-[:BELONGS_TO]-(:Entity {id: orig})
        }
        RETURN collect(DISTINCT e2.id) AS ids
        """,
        u1=source_universe_id,
        u2=target_universe_id,
    )

    # Facts
    f_src = repo.run(
        """
        MATCH (:Universe {id:$u1})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(:Scene)<-[:OCCURS_IN]-(f:Fact)
        WHERE NOT EXISTS {
            MATCH (:Universe {id:$u2})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(:Scene)<-[:OCCURS_IN]-(:Fact {id:$u2 + '/' + f.id})
        }
        RETURN collect(DISTINCT f.id) AS ids
        """,
        u1=source_universe_id,
        u2=target_universe_id,
    )
    f_tgt = repo.run(
        """
        MATCH (:Universe {id:$u2})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(:Scene)<-[:OCCURS_IN]-(f2:Fact)
        WITH f2,
             CASE WHEN f2.id STARTS WITH $u2 + '/' THEN substring(f2.id, size($u2)+1) ELSE f2.id END AS orig
        WHERE NOT EXISTS {
            MATCH (:Universe {id:$u1})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(:Scene)<-[:OCCURS_IN]-(:Fact {id: orig})
        }
        RETURN collect(DISTINCT f2.id) AS ids
        """,
        u1=source_universe_id,
        u2=target_universe_id,
    )

    def _ids(res: list[dict[str, Any]]) -> list[str]:
        return list(res[0].get("ids", [])) if res else []

    # Provenance counts: nodes in target branched from nodes in source
    prov = {
        "stories": int(
            (
                repo.run(
                    """
                MATCH (:Universe {id:$u2})-[:HAS_STORY]->(st2:Story)-[:BRANCHED_FROM]->(st:Story)
                MATCH (:Universe {id:$u1})-[:HAS_STORY]->(st)
                RETURN count(DISTINCT st2) AS c
                """,
                    u1=source_universe_id,
                    u2=target_universe_id,
                )
                or [{"c": 0}]
            )[0]["c"]
        ),
        "scenes": int(
            (
                repo.run(
                    """
                MATCH (:Universe {id:$u2})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(sc2:Scene)-[:BRANCHED_FROM]->(sc:Scene)
                MATCH (:Universe {id:$u1})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(sc)
                RETURN count(DISTINCT sc2) AS c
                """,
                    u1=source_universe_id,
                    u2=target_universe_id,
                )
                or [{"c": 0}]
            )[0]["c"]
        ),
        "entities": int(
            (
                repo.run(
                    """
                MATCH (:Universe {id:$u2})<-[:BELONGS_TO]-(e2:Entity)-[:BRANCHED_FROM]->(e:Entity)
                MATCH (:Universe {id:$u1})<-[:BELONGS_TO]-(e)
                RETURN count(DISTINCT e2) AS c
                """,
                    u1=source_universe_id,
                    u2=target_universe_id,
                )
                or [{"c": 0}]
            )[0]["c"]
        ),
        "facts": int(
            (
                repo.run(
                    """
                MATCH (:Universe {id:$u2})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(:Scene)<-[:OCCURS_IN]-(f2:Fact)-[:BRANCHED_FROM]->(f:Fact)
                MATCH (:Universe {id:$u1})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(:Scene)<-[:OCCURS_IN]-(f)
                RETURN count(DISTINCT f2) AS c
                """,
                    u1=source_universe_id,
                    u2=target_universe_id,
                )
                or [{"c": 0}]
            )[0]["c"]
        ),
    }

    return TypedDiffRes(
        source_universe_id=source_universe_id,
        target_universe_id=target_universe_id,
        stories=TypedList(only_in_source=_ids(st_src), only_in_target=_ids(st_tgt)),
        scenes=TypedList(only_in_source=_ids(sc_src), only_in_target=_ids(sc_tgt)),
        entities=TypedList(only_in_source=_ids(e_src), only_in_target=_ids(e_tgt)),
        facts=TypedList(only_in_source=_ids(f_src), only_in_target=_ids(f_tgt)),
        provenance=ProvenanceCounts(**prov),
    )


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
            q = """
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
            rows = repo.run(q, source=req.source_universe_id, target=req.target_universe_id)
            inserted = int(rows[0]["inserted"]) if rows else 0
            return {"ok": True, "inserted": inserted}
        elif req.strategy == "append_missing":
            # Append links from source nodes into target universe, idempotently.
            # Namespaced branch ids remain unique in target.
            ops = 0
            # Stories
            rows = repo.run(
                """
                MATCH (:Universe {id:$src})-[:HAS_STORY]->(st:Story)
                WITH DISTINCT st
                MATCH (u2:Universe {id:$tgt})
                MERGE (u2)-[:HAS_STORY]->(st)
                RETURN count(DISTINCT st) AS c
                """,
                src=req.source_universe_id,
                tgt=req.target_universe_id,
            )
            ops += int(rows[0]["c"]) if rows else 0
            # Scenes
            rows = repo.run(
                """
                MATCH (:Universe {id:$src})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
                WITH DISTINCT st, sc
                MATCH (:Universe {id:$tgt})-[:HAS_STORY]->(st)
                MERGE (st)-[:HAS_SCENE {sequence_index: coalesce(sc.sequence_index, 0)}]->(sc)
                RETURN count(DISTINCT sc) AS c
                """,
                src=req.source_universe_id,
                tgt=req.target_universe_id,
            )
            ops += int(rows[0]["c"]) if rows else 0
            # Entities -> target universe
            rows = repo.run(
                """
                MATCH (:Universe {id:$src})<-[:BELONGS_TO]-(e:Entity)
                WITH DISTINCT e
                MATCH (u2:Universe {id:$tgt})
                MERGE (e)-[:BELONGS_TO]->(u2)
                RETURN count(DISTINCT e) AS c
                """,
                src=req.source_universe_id,
                tgt=req.target_universe_id,
            )
            ops += int(rows[0]["c"]) if rows else 0
            # Entity APPEARS_IN edges for scenes attached in target
            rows = repo.run(
                """
                MATCH (:Universe {id:$src})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(sc:Scene)
                MATCH (e:Entity)-[:APPEARS_IN]->(sc)
                WITH DISTINCT e, sc
                MATCH (:Universe {id:$tgt})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(sc)
                MERGE (e)-[:APPEARS_IN]->(sc)
                RETURN count(DISTINCT e) AS c
                """,
                src=req.source_universe_id,
                tgt=req.target_universe_id,
            )
            ops += int(rows[0]["c"]) if rows else 0
            # Facts -> scenes in target
            rows = repo.run(
                """
                MATCH (:Universe {id:$src})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(sc:Scene)
                MATCH (f:Fact)-[:OCCURS_IN]->(sc)
                WITH DISTINCT f, sc
                MATCH (:Universe {id:$tgt})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(sc)
                MERGE (f)-[:OCCURS_IN]->(sc)
                RETURN count(DISTINCT f) AS c
                """,
                src=req.source_universe_id,
                tgt=req.target_universe_id,
            )
            ops += int(rows[0]["c"]) if rows else 0
            # Sheets for entities (carry over to target by ensuring HAS_SHEET edges are present)
            rows = repo.run(
                """
                MATCH (:Universe {id:$src})<-[:BELONGS_TO]-(e:Entity)-[hs:HAS_SHEET]->(sh:Sheet)
                WITH DISTINCT e, sh, hs
                MATCH (:Universe {id:$tgt})<-[:BELONGS_TO]-(e)
                MERGE (e)-[hs2:HAS_SHEET]->(sh)
                SET hs2.story_id = hs.story_id, hs2.system_id = hs.system_id
                RETURN count(DISTINCT sh) AS c
                """,
                src=req.source_universe_id,
                tgt=req.target_universe_id,
            )
            ops += int(rows[0]["c"]) if rows else 0
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
