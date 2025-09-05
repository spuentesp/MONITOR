from __future__ import annotations

from core.agents.base import Agent
from core.agents.registry import AgentRegistry


@AgentRegistry.register("Conductor", temperature=0.1, max_tokens=8)
def conductor_prompt():
    """Conductor agent prompt."""
    return (
        "You are Conductor. Given a compact state snapshot and a list of allowed next steps,\n"
        "choose exactly ONE next label and return ONLY that label (no punctuation).\n"
        "Prefer steps that improve coherence and correctness."
    )


# Legacy compatibility function
def conductor_agent(llm) -> Agent:
    """Legacy compatibility: create conductor agent."""
    return AgentRegistry.create_agent("conductor", llm)
