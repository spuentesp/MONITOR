"""Modular branches API with focused endpoint groups.

This package splits the original monolithic branches_api.py into focused modules:

- models: All Pydantic request/response models
- utils: Common utilities and service factories  
- branching_endpoints: Branch and clone operations
- diff_endpoints: Universe comparison operations
- promotion_endpoints: Branch promotion operations

This modular approach follows Single Responsibility Principle and makes
the codebase more maintainable and testable.
"""

from fastapi import APIRouter

from .branching_endpoints import router as branching_router
from .diff_endpoints import router as diff_router
from .promotion_endpoints import router as promotion_router

# Assemble all endpoints under the /branches prefix
router = APIRouter(prefix="/branches", tags=["branches"])

# Include all endpoint groups
router.include_router(branching_router)
router.include_router(diff_router)
router.include_router(promotion_router)

__all__ = ["router"]
