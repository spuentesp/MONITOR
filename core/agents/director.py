from __future__ import annotations

from core.agents.base import Agent, AgentConfig
from core.loaders.agent_prompts import load_agent_prompts


def director_agent(llm) -> Agent:
    prompts = load_agent_prompts()
    sys = prompts.get(
        "director",
        "You are Director. Turn a user intent into a tiny actionable plan: 2-4 bullet beats,"
        " key assumptions, and immediate next step. Be brief and concrete.",
    )
    return Agent(AgentConfig(name="Director", system_prompt=sys, llm=llm, temperature=0.3, max_tokens=220))
