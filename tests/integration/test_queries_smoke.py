import os

import pytest

from core.persistence.neo4j_repo import Neo4jRepo
from core.persistence.queries import QueryService


def neo4j_env_present():
    return all(os.getenv(k) for k in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASS"))


@pytest.mark.skipif(not neo4j_env_present(), reason="Neo4j env not configured for integration test")
def test_queries_execute_without_error():
    repo = Neo4jRepo().connect()
    svc = QueryService(repo)
    assert isinstance(svc.entities_in_scene("non-existent"), list)
    assert isinstance(svc.facts_for_scene("non-existent"), list)
    assert isinstance(svc.relation_state_history("e1", "e2"), list)
    assert isinstance(svc.axioms_applying_to_universe("u1"), list)
    assert isinstance(svc.scenes_for_entity("e1"), list)
    repo.close()
