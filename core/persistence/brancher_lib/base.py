from __future__ import annotations

from typing import Any

try:
    from core.ports.storage import RepoPort  # type: ignore
except Exception:  # pragma: no cover
    RepoPort = Any  # type: ignore

class BranchBase:
    def __init__(self, repo: RepoPort | Any):
        self.repo = repo

    def _check_source_and_target(
        self, source_universe_id: str, new_universe_id: str, force: bool
    ) -> None:
        rows = self.repo.run(
            """
            OPTIONAL MATCH (src:Universe {id:$src})
            OPTIONAL MATCH (tgt:Universe {id:$tgt})
            RETURN src IS NOT NULL AS src_ok, tgt IS NOT NULL AS tgt_exists
            """,
            src=source_universe_id,
            tgt=new_universe_id,
        )
        src_ok = rows and rows[0].get("src_ok", False)
        tgt_exists = rows and rows[0].get("tgt_exists", False)
        if not src_ok:
            raise ValueError("Source universe not found")
        if tgt_exists and not force:
            raise ValueError(
                "Target universe already exists; use --force to overwrite or choose a new id"
            )

    @staticmethod
    def _first_count(rows: list[dict[str, Any]] | list[Any]) -> int:
        return int(rows[0]["c"]) if rows and "c" in rows[0] else 0
