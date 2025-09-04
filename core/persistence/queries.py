from __future__ import annotations

from typing import Any

try:
    from core.ports.storage import RepoPort  # type: ignore
except Exception:  # pragma: no cover
    RepoPort = Any  # type: ignore

from core.persistence.queries.axioms import AxiomsQueries
from core.persistence.queries.base import BaseQueries
from core.persistence.queries.catalog import CatalogQueries
from core.persistence.queries.entities import EntitiesQueries
from core.persistence.queries.facts import FactsQueries
from core.persistence.queries.relations import RelationsQueries
from core.persistence.queries.scenes import ScenesQueries
from core.persistence.queries.systems import SystemsQueries


class QueryService(
    BaseQueries,
    EntitiesQueries,
    ScenesQueries,
    FactsQueries,
    RelationsQueries,
    AxiomsQueries,
    SystemsQueries,
    CatalogQueries,
):
    def __init__(self, repo: RepoPort | Any):
        super().__init__(repo)  # BaseQueries expects a repo duck-typed to RepoPort
