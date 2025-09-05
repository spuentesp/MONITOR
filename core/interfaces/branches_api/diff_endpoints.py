"""Diff endpoints for comparing universes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from core.persistence.neo4j_repo import Neo4jRepo

from .models import DiffRes, ProvenanceCounts, TypedDiffRes, TypedList

router = APIRouter()


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
        provenance_counts=ProvenanceCounts(**prov),
    )
