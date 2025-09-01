from __future__ import annotations

from core.agents.base import Agent, AgentConfig
from core.loaders.agent_prompts import load_agent_prompts


def archivist_agent(llm) -> Agent:
    prompts = load_agent_prompts()
    sys = prompts.get(
        "archivist",
        "You are Archivist, a lore librarian. Answer briefly with bullet points, summarize events so far, "
        "and note open threads or inconsistencies.",
    )
    return Agent(
        AgentConfig(name="Archivist", system_prompt=sys, llm=llm, temperature=0.4, max_tokens=300)
    )
