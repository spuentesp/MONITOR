from __future__ import annotations

from .base import BaseQueries
from .entities import EntitiesQueries
from .scenes import ScenesQueries
from .facts import FactsQueries
from .relations import RelationsQueries
from .axioms import AxiomsQueries
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
