from __future__ import annotations

from typing import Any

try:
    from core.ports.storage import RepoPort  # type: ignore
except Exception:  # pragma: no cover
    RepoPort = Any  # type: ignore

from core.persistence.queries_lib.axioms import AxiomsQueries
from core.persistence.queries_lib.base import BaseQueries
from core.persistence.queries_lib.catalog import CatalogQueries
from core.persistence.queries_lib.entities import EntitiesQueries
from core.persistence.queries_lib.facts import FactsQueries
from core.persistence.queries_lib.relations import RelationsQueries
from core.persistence.queries_lib.scenes import ScenesQueries
from core.persistence.queries_lib.systems import SystemsQueries


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
