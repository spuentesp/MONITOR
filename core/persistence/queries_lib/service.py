from __future__ import annotations

from .axioms import AxiomsQueries
from .base import BaseQueries
from .entities import EntitiesQueries
from .facts import FactsQueries
from .relations import RelationsQueries
from .scenes import ScenesQueries
from .systems import SystemsQueries


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
