from __future__ import annotations

from core.agents.base import Agent, AgentConfig
from core.loaders.agent_prompts import load_agent_prompts


def librarian_agent(llm) -> Agent:
    prompts = load_agent_prompts()
    sys = prompts.get(
        "librarian",
        "You are Librarian. Retrieve and summarize relevant story context (entities, scenes, relations)."
        " Be concise and return only the most useful details for the next beat.",
    )
    return Agent(
        AgentConfig(name="Librarian", system_prompt=sys, llm=llm, temperature=0.2, max_tokens=220)
    )
