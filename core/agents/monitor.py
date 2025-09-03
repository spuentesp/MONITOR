from __future__ import annotations

from core.agents.base import Agent, AgentConfig
from core.loaders.agent_prompts import load_agent_prompts


def monitor_agent(llm) -> Agent:
    prompts = load_agent_prompts()
    sys = prompts.get(
        "monitor",
        "You are Monitor. Decide if the user intent is narrative or operational."
        " Route narrative to the Narrator; route data lookup to the Archivist."
        " For ops, be precise and ask for missing IDs. Keep answers short.",
    )
    return Agent(
        AgentConfig(name="Monitor", system_prompt=sys, llm=llm, temperature=0.1, max_tokens=180)
    )
