from __future__ import annotations

from core.agents.base import Agent
from core.agents.registry import AgentRegistry


@AgentRegistry.register("Narrator", temperature=0.8, max_tokens=350)
def narrator_prompt():
    """Narrator agent prompt."""
    return (
        "You are Narrator, a concise, evocative Game Master.\n"
        "- Stay in the current scene/time unless the user explicitly moves.\n"
        "- Do not relocate or add new entities unless requested.\n"
        "- Write a short, sensory beat and ask 1 guiding question.\n"
        "- Keep continuity with known participants and tags.\n"
        "- Avoid long exposition."
    )


# Legacy compatibility function
def narrator_agent(llm) -> Agent:
    """Legacy compatibility: create narrator agent."""
    return AgentRegistry.create_agent("narrator", llm)
