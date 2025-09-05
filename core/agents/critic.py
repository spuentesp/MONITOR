from __future__ import annotations

from core.agents.base import Agent
from core.agents.registry import AgentRegistry


@AgentRegistry.register("Critic", temperature=0.2, max_tokens=180)
def critic_prompt():
    """Critic agent prompt."""
    return (
        "You are Critic. Score the draft on clarity, pacing, and hook. Suggest 1-2 crisp improvements. "
        "Avoid rewriting unless asked."
    )


# Legacy compatibility function
def critic_agent(llm) -> Agent:
    """Legacy compatibility: create critic agent."""
    return AgentRegistry.create_agent("critic", llm)
