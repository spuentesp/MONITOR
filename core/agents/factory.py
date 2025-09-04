from __future__ import annotations

from typing import Any, Dict

from .archivist import archivist_agent
from .conductor import conductor_agent
from .continuity import continuity_agent
from .critic import critic_agent
from .director import director_agent
from .intent_router import intent_router_agent
from .librarian import librarian_agent
from .narrator import narrator_agent
from .planner import planner_agent
from .qa import qa_agent
from .steward import steward_agent


def build_agents(llm: Any) -> Dict[str, Any]:
    """Construct and return all LLM-backed agents keyed by their canonical names.

    Keeps agent wiring in one place to avoid duplication in orchestrators/flows.
    """
    return {
        "narrator": narrator_agent(llm),
        "archivist": archivist_agent(llm),
        "director": director_agent(llm),
        "librarian": librarian_agent(llm),
        "steward": steward_agent(llm),
        "critic": critic_agent(llm),
        "intent_router": intent_router_agent(llm),
        "planner": planner_agent(llm),
        "qa": qa_agent(llm),
        "continuity": continuity_agent(llm),
        "conductor": conductor_agent(llm),
    }
