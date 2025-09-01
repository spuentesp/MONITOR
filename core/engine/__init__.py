from __future__ import annotations

from core.agents.base import Session
from core.agents.narrador import narrator_agent


def default_narrative_session(llm) -> Session:
    return Session(primary=narrator_agent(llm))
