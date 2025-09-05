from __future__ import annotations

from core.agents.base import Agent
from core.agents.registry import AgentRegistry


@AgentRegistry.register("Steward", temperature=0.1, max_tokens=180)
def steward_prompt():
    """Steward agent prompt."""
    return (
        "You are Steward. Validate coherence and policy. Flag missing IDs, continuity breaks, "
        "or ontology write risks. Be terse and practical with fixes."
    )


# Legacy compatibility function
def steward_agent(llm) -> Agent:
    """Legacy compatibility: create steward agent."""
    return AgentRegistry.create_agent("steward", llm)
