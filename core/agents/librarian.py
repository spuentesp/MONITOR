from __future__ import annotations

from core.agents.base import Agent
from core.agents.registry import AgentRegistry


@AgentRegistry.register("Librarian", temperature=0.2, max_tokens=220)
def librarian_prompt():
    """Librarian agent prompt."""
    return (
        "You are Librarian. Retrieve and summarize relevant story context (entities, scenes, relations). "
        "Be concise and return only the most useful details for the next beat."
    )


# Legacy compatibility function
def librarian_agent(llm) -> Agent:
    """Legacy compatibility: create librarian agent."""
    return AgentRegistry.create_agent("librarian", llm)
