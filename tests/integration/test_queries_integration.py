import pytest
pytestmark = pytest.mark.integration

from core.persistence.neo4j_repo import Neo4jRepo
from core.persistence.projector import Projector
from core.persistence.queries import QueryService


def neo4j_available():
    try:
        Neo4jRepo().connect().close()
        return True
    except Exception:
        return False


requires_neo4j = pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")


@pytest.fixture(scope="module")
def populated_db():
    repo = Neo4jRepo().connect()
    repo.run("MATCH (n) DETACH DELETE n")
    repo.bootstrap_constraints()
    from tests.data import example_multiverse  # type: ignore  # ensure package discoverable
    import pathlib
    yaml_path = pathlib.Path(__file__).resolve().parents[2] / "tests" / "data" / "example_multiverse.yaml"
    Projector(repo).project_from_yaml(yaml_path, ensure_constraints=False)
    yield repo
    repo.close()


@requires_neo4j
def test_queries_cover_core_paths(populated_db):
    q = QueryService(populated_db)
    any_story = populated_db.run("MATCH (s:Story) RETURN s.id as sid LIMIT 1")[0]["sid"]
    any_scene = populated_db.run("MATCH (sc:Scene) RETURN sc.id as scid LIMIT 1")[0]["scid"]
    any_universe = populated_db.run("MATCH (u:Universe) RETURN u.id as uid LIMIT 1")[0]["uid"]

    ents_scene = q.entities_in_scene(any_scene)
    ents_story = q.entities_in_story(any_story)
    ents_univ = q.entities_in_universe(any_universe)

    assert isinstance(ents_scene, list)
    assert isinstance(ents_story, list)
    assert isinstance(ents_univ, list)

    facts_story = q.facts_for_story(any_story)
    facts_scene = q.facts_for_scene(any_scene)
    assert all({"id", "description", "participants"} <= set(f) for f in facts_story)
    assert all({"id", "description", "participants"} <= set(f) for f in facts_scene)

    ids = populated_db.run(
        "MATCH (a:Entity)-[:APPEARS_IN]->(:Scene)<-[:OCCURS_IN]-(:Fact)<-[:PARTICIPATES_AS]-(:Entity) RETURN a.id as a LIMIT 1"
    )
    if ids:
        ent_a = ids[0]["a"]
        rh = q.relation_state_history(ent_a, ent_a)
        assert isinstance(rh, list)

    axs = q.axioms_applying_to_universe(any_universe)
    ax_in_sc = q.axioms_effective_in_scene(any_scene)
    assert isinstance(axs, list) and isinstance(ax_in_sc, list)

    sys_sum = q.system_usage_summary(any_universe)
    assert isinstance(sys_sum, list)

    eff_u = q.effective_system_for_universe(any_universe)
    eff_story = q.effective_system_for_story(any_story)
    eff_scene = q.effective_system_for_scene(any_scene)
    assert eff_u is None or set(eff_u.keys()) == {"system_id", "source"}
    assert eff_story is None or set(eff_story.keys()) == {"system_id", "source"}
    assert eff_scene is None or set(eff_scene.keys()) == {"system_id", "source"}

    any_entity = populated_db.run(
        "MATCH (e:Entity)-[:HAS_SHEET]->(:Sheet) RETURN e.id AS eid LIMIT 1"
    )[0]["eid"]
    eff_e = q.effective_system_for_entity(any_entity)
    assert eff_e is None or (eff_e["system_id"] and eff_e["source"] in {"entity", "sheet"})
    eff_e_story = q.effective_system_for_entity_in_story(any_entity, any_story)
    assert eff_e_story is None or eff_e_story["system_id"]

    rels_active = q.relations_effective_in_scene(any_scene)
    assert isinstance(rels_active, list)
