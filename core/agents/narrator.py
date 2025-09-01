from __future__ import annotations

from core.agents.base import Agent, AgentConfig
from core.loaders.agent_prompts import load_agent_prompts


def narrator_agent(llm) -> Agent:
    prompts = load_agent_prompts()
    sys = prompts.get(
        "narrator",
        "You are Narrator, a concise, evocative Game Master. Write short, scene-focused narrative beats, "
        "ask 1 guiding question, and keep continuity. Avoid long expository dumps.",
    )
    return Agent(
        AgentConfig(name="Narrator", system_prompt=sys, llm=llm, temperature=0.8, max_tokens=350)
    )
