"""Common utilities for branches API endpoints."""

from core.persistence.neo4j_repo import Neo4jRepo
from core.services.branching.brancher_service import BrancherService


def get_brancher_service() -> BrancherService:
    """Create and return a BrancherService instance."""
    repo = Neo4jRepo().connect()
    return BrancherService(repo)
