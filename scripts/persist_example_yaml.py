from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # noqa: E402

from core.persistence.neo4j_repo import Neo4jRepo  # noqa: E402
from core.persistence.projector import Projector  # noqa: E402

yaml_path = Path(__file__).resolve().parents[1] / "tests" / "data" / "example_multiverse.yaml"

repo = Neo4jRepo().connect()
print(f"Connected to {repo.uri} as {repo.user}")
print("Bootstrapping constraints...")
repo.bootstrap_constraints()
print("Projecting from YAML...")
Projector(repo).project_from_yaml(yaml_path, ensure_constraints=False)
print("Done.")

# Quick smoke check: count a few labels
counts = {}
for label in [
    "Omniverse",
    "Multiverse",
    "Universe",
    "Story",
    "Scene",
    "Entity",
    "Sheet",
    "Axiom",
    "Arc",
    "Fact",
    "RelationState",
    "System",
]:
    rows = repo.run(f"MATCH (n:{label}) RETURN count(n) AS c")
    counts[label] = rows[0]["c"] if rows else 0
print("Counts:")
for k, v in counts.items():
    print(f"  {k}: {v}")
