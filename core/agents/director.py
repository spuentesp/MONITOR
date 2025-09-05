from __future__ import annotations

from core.agents.base import Agent
from core.agents.registry import AgentRegistry


@AgentRegistry.register("Director", temperature=0.3, max_tokens=220)
def director_prompt():
    """Director agent prompt."""
    return (
        "You are Director. Turn a user intent into a tiny actionable plan: 2-4 bullet beats, "
        "key assumptions, and immediate next step. Be brief and concrete."
    )


# Legacy compatibility function
def director_agent(llm) -> Agent:
    """Legacy compatibility: create director agent."""
    return AgentRegistry.create_agent("director", llm)
