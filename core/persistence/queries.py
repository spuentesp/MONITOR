from __future__ import annotations

from core.persistence.queries_lib.axioms import AxiomsQueries
from core.persistence.queries_lib.base import BaseQueries
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
):
    def __init__(self, repo):
        super().__init__(repo)
