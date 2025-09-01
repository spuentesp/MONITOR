import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.persistence.projector import Projector  # noqa: E402


class FakeRepo:
    def __init__(self):
        self.cyphers = []
        self.constraints = False

    def connect(self):
        return self

    def close(self):
        pass

    def run(self, cypher: str, **params):
        # Normalize whitespace for easier assertions
        self.cyphers.append((" ".join(cypher.split()), params))
        return []

    def ping(self):
        return True

    def bootstrap_constraints(self):
        self.constraints = True


def test_projector_projects_all_node_types_and_relations(tmp_path: Path):
    yaml_path = ROOT / "tests" / "data" / "example_multiverse.yaml"
    repo = FakeRepo()
    p = Projector(repo)
    p.project_from_yaml(yaml_path, ensure_constraints=True)

    # Constraints were ensured
    assert repo.constraints is True
    # Check that essential labels were merged at least once
    merged_labels = "\n".join(c for c, _ in repo.cyphers)
    for label in [
        "MERGE (o:Omniverse",
        "MERGE (m:Multiverse",
        "MERGE (u:Universe",
        "MERGE (a:Arc",
        "MERGE (s:Story",
        "MERGE (sc:Scene",
        "MERGE (e:Entity",
        "MERGE (s:Sheet",
        "MERGE (a:Axiom",
        "MERGE (sys:System",
    ]:
        assert label in merged_labels

    # Relationship patterns expected
    expected_relationship_snippets = [
        ":HAS_UNIVERSE",
        ":HAS_ARC",
        ":HAS_STORY",
        ":HAS_SCENE",
        ":BELONGS_TO",
        ":HAS_SHEET",
        ":APPEARS_IN",
        ":OCCURS_IN",
        ":PARTICIPATES_AS",
        ":REL_STATE_FOR",
        ":REFERS_TO",
        ":APPLIES_TO",
    ]
    text = "\n".join(c for c, _ in repo.cyphers)
    for snippet in expected_relationship_snippets:
        assert snippet in text
