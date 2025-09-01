from __future__ import annotations

from typing import Any, Dict

from core.persistence.neo4j_repo import Neo4jRepo
from core.persistence.brancher_lib.base import BranchBase
from core.persistence.brancher_lib.branch_at_scene import BranchAtSceneMixin
from core.persistence.brancher_lib.clone_full import CloneFullMixin
from core.persistence.brancher_lib.clone_subset import CloneSubsetMixin


class BranchService(BranchBase, BranchAtSceneMixin, CloneFullMixin, CloneSubsetMixin):
    """
    What-if branching and cloning operations for Universes.
    Public entry point; method implementations live in mixins under brancher_lib/.
    """

    def __init__(self, repo: Neo4jRepo):
        super().__init__(repo)
