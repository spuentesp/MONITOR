from __future__ import annotations

from typing import Any

# Import agents to trigger registration
from .registry import AgentRegistry


def build_agents(llm: Any) -> dict[str, Any]:
    """Construct and return all LLM-backed agents keyed by their canonical names.

    Now uses the extensible AgentRegistry system to eliminate duplication
    and enable adding new agents without modifying existing code.
    """
    # Build all registered agents
    agents = AgentRegistry.build_all_agents(llm)

    # Map registry keys to expected factory keys for backward compatibility
    return {
        "narrator": agents.get("narrator"),
        "archivist": agents.get("archivist"),
        "director": agents.get("director"),
        "librarian": agents.get("librarian"),
        "steward": agents.get("steward"),
        "critic": agents.get("critic"),
        "intent_router": agents.get("intentrouter"),
        "planner": agents.get("planner"),
        "qa": agents.get("qa"),
        "continuity": agents.get("continuitymoderator"),
        "conductor": agents.get("conductor"),
    }
