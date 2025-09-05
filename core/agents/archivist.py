from __future__ import annotations

from core.agents.base import Agent
from core.agents.registry import AgentRegistry


@AgentRegistry.register("Archivist", temperature=0.4, max_tokens=300)
def archivist_prompt():
    """Archivist agent prompt."""
    return (
        "You are Archivist, a lore librarian. Answer briefly with bullet points, summarize events so far, "
        "and note open threads or inconsistencies."
    )


# Legacy compatibility function
def archivist_agent(llm) -> Agent:
    """Legacy compatibility: create archivist agent."""
    return AgentRegistry.create_agent("archivist", llm)
