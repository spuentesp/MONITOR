from __future__ import annotations

from core.agents.base import Agent, AgentConfig
from core.loaders.agent_prompts import load_agent_prompts


def resolve_agent(llm) -> Agent:
    prompts = load_agent_prompts()
    sys = prompts.get(
        "resolve",
        (
            "You are Resolve. Given proposed deltas, validation results, and mode, decide whether to commit now or stage.\n"
            "Return ONLY JSON: {\"commit\": <true|false>, \"reason\": <short>, \"fixes\": <optional obj>}"
        ),
    )
    return Agent(AgentConfig(name="Resolve", system_prompt=sys, llm=llm, temperature=0.2, max_tokens=200))
