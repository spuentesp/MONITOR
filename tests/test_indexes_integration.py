from pathlib import Path
import sys

import pytest
pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.persistence.neo4j_repo import Neo4jRepo  # noqa: E402


def neo4j_available():
    try:
        Neo4jRepo().connect().close()
        return True
    except Exception:
        return False


requires_neo4j = pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")


@requires_neo4j
def test_bootstrap_indexes_exist():
    repo = Neo4jRepo().connect()
    try:
        repo.bootstrap_constraints()
        repo.bootstrap_indexes()
        # List indexes from db. Index names are auto-generated; check by entity and properties
        rows = repo.run(
            "SHOW INDEXES YIELD entityType, labelsOrTypes, properties RETURN entityType, labelsOrTypes, properties"
        )
        # Some rows may have nulls depending on DB version/config; keep only those with labels/types and properties
        sig_rows = [r for r in rows if r.get("labelsOrTypes") and r.get("properties")]
        by_sig = {
            (r["entityType"], tuple(r["labelsOrTypes"]), tuple(r["properties"])) for r in sig_rows
        }
        assert ("NODE", ("Scene",), ("sequence_index",)) in by_sig
        assert ("NODE", ("Story",), ("arc_id",)) in by_sig
        assert ("NODE", ("Scene",), ("story_id",)) in by_sig
        assert ("RELATIONSHIP", ("HAS_SCENE",), ("sequence_index",)) in by_sig
    finally:
        repo.close()
