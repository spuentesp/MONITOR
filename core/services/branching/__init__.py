"""
Branching services package.

This package provides universe cloning and branching operations
using a composition-based architecture.
"""

from core.services.branching.brancher_service import BrancherService
from core.services.branching.universe_brancher import UniverseBrancher
from core.services.branching.universe_cloner import UniverseCloner

__all__ = [
    "BrancherService",
    "UniverseBrancher", 
    "UniverseCloner",
]
