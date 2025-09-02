from __future__ import annotations

from core.agents.base import Agent, AgentConfig
from core.loaders.agent_prompts import load_agent_prompts


def conductor_agent(llm) -> Agent:
    prompts = load_agent_prompts()
    sys = prompts.get(
        "conductor",
        (
            "You are Conductor. Given a compact state snapshot and a list of allowed next steps,\n"
            "choose exactly ONE next label and return ONLY that label (no punctuation).\n"
            "Prefer steps that improve coherence and correctness."
        ),
    )
    return Agent(AgentConfig(name="Conductor", system_prompt=sys, llm=llm, temperature=0.1, max_tokens=8))
