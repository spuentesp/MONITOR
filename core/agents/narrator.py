from __future__ import annotations

from core.agents.base import Agent, AgentConfig
from core.loaders.agent_prompts import load_agent_prompts


def narrator_agent(llm) -> Agent:
    prompts = load_agent_prompts()
    sys = prompts.get(
        "narrator",
        "You are Narrator, a concise, evocative Game Master.\n"
        "- Stay in the current scene/time unless the user explicitly moves.\n"
        "- Do not relocate or add new entities unless requested.\n"
        "- Write a short, sensory beat and ask 1 guiding question.\n"
        "- Keep continuity with known participants and tags.\n"
        "- Avoid long exposition.",
    )
    return Agent(
        AgentConfig(name="Narrator", system_prompt=sys, llm=llm, temperature=0.8, max_tokens=350)
    )
