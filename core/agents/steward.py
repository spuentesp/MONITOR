from __future__ import annotations

from core.agents.base import Agent, AgentConfig
from core.loaders.agent_prompts import load_agent_prompts


def steward_agent(llm) -> Agent:
    prompts = load_agent_prompts()
    sys = prompts.get(
        "steward",
        "You are Steward. Validate coherence and policy. Flag missing IDs, continuity breaks,"
        " or ontology write risks. Be terse and practical with fixes.",
    )
    return Agent(
        AgentConfig(name="Steward", system_prompt=sys, llm=llm, temperature=0.1, max_tokens=180)
    )
