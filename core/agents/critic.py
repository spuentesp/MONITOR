from __future__ import annotations

from core.agents.base import Agent, AgentConfig
from core.loaders.agent_prompts import load_agent_prompts


def critic_agent(llm) -> Agent:
    prompts = load_agent_prompts()
    sys = prompts.get(
        "critic",
        "You are Critic. Score the draft on clarity, pacing, and hook. Suggest 1-2 crisp improvements."
        " Avoid rewriting unless asked.",
    )
    return Agent(
        AgentConfig(name="Critic", system_prompt=sys, llm=llm, temperature=0.2, max_tokens=180)
    )
