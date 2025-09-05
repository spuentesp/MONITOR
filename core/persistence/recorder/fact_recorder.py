"""Fact persistence operations with evidence and source management."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from .utils import ensure_id, sanitize_value


class FactRecorder:
    """Handle fact creation, linking, and evidence/source management."""

    def __init__(self, repo: Any):
        self.repo = repo

    def create_facts(
        self, 
        facts: list[dict[str, Any]], 
        scene_id: str | None, 
        universe_id: str | None
    ) -> int:
        """Create facts with scene linking and evidence/source management."""
        rows = []
        ev_rows: list[dict[str, Any]] = []
        
        for f in facts:
            fid = ensure_id("fact", f.get("id"))
            # Enforce provenance: require a scene_id either per fact or defaulted from request
            occurs_in = f.get("occurs_in") or scene_id
            if not occurs_in:
                raise ValueError(
                    "Fact commit requires a scene context (occurs_in or default scene_id)."
                )
            props = {
                "universe_id": f.get("universe_id") or universe_id,
                "description": f.get("description"),
                "when": f.get("when"),
                "time_span": sanitize_value(f.get("time_span")),
                "confidence": f.get("confidence"),
                "derived_from": sanitize_value(f.get("derived_from")),
            }
            participants = f.get("participants", [])
            rows.append(
                {
                    "id": fid,
                    "props": props,
                    "occurs_in": occurs_in,
                    "participants": participants,
                }
            )
            
            # Optional evidence promotion to :Source
            evidence = f.get("evidence") or []
            if evidence:
                sources: list[dict[str, Any]] = []
                for e in evidence:
                    if isinstance(e, str):
                        doc_id = e
                        sid = f"source:{doc_id}"
                        sources.append({"id": sid, "doc_id": doc_id})
                    elif isinstance(e, dict):
                        dict_doc_id = e.get("doc_id")
                        if not isinstance(dict_doc_id, str):
                            dict_doc_id = ""
                        sid = e.get("id") or (
                            f"source:{dict_doc_id}" if dict_doc_id else f"source:{uuid4()}"
                        )
                        sources.append(
                            {
                                "id": sid,
                                "doc_id": dict_doc_id,
                                "title": e.get("title"),
                                "kind": e.get("kind"),
                                "minio_key": e.get("minio_key"),
                                "metadata": sanitize_value(e.get("metadata")),
                            }
                        )
                if sources:
                    ev_rows.append({"fact_id": fid, "sources": sources})
        
        # Create facts and link to scenes
        self.repo.run(
            """
            UNWIND $rows AS row
            MERGE (f:Fact {id: row.id})
            SET f += row.props
            WITH row, f
            OPTIONAL MATCH (sc:Scene {id: row.occurs_in})
            FOREACH (_ IN CASE WHEN sc IS NULL THEN [] ELSE [1] END | MERGE (f)-[:OCCURS_IN]->(sc))
            """,
            rows=rows,
        )
        
        # Create participant relationships
        self.repo.run(
            """
            UNWIND $rows AS row
            MATCH (f:Fact {id: row.id})
            UNWIND row.participants AS p
            MATCH (e:Entity {id: p.entity_id})
            MERGE (e)-[:PARTICIPATES_AS {role: p.role}]->(f)
            """,
            rows=rows,
        )
        
        # Create evidence/source relationships
        if ev_rows:
            self.repo.run(
                """
                UNWIND $rows AS row
                MATCH (f:Fact {id: row.fact_id})
                UNWIND row.sources AS src
                MERGE (s:Source {id: src.id})
                SET s.doc_id = coalesce(src.doc_id, s.doc_id),
                    s.title = coalesce(src.title, s.title),
                    s.kind = coalesce(src.kind, s.kind),
                    s.minio_key = coalesce(src.minio_key, s.minio_key),
                    s.metadata = coalesce(src.metadata, s.metadata)
                MERGE (f)-[:SUPPORTED_BY]->(s)
                """,
                rows=ev_rows,
            )
        
        return len(rows)
