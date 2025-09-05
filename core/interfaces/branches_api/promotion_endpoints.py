"""Promotion endpoints for merging branch changes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from core.utils.http_exceptions import bad_request_from_exception

from core.persistence.neo4j_repo import Neo4jRepo

from .models import PromoteReq

router = APIRouter()


@router.post("/promote")
def promote_branch(req: PromoteReq) -> dict[str, Any]:
    """Promote changes from a branch to a target universe.

    MVP strategy: append Facts that don't exist in target; skip collisions. Overwrite option replaces properties.
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
            return {"ok": False, "error": "Unknown strategy"}
    except Exception as e:
        raise bad_request_from_exception(e) from e
