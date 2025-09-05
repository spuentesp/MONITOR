from __future__ import annotations

from core.agents.base import Agent, AgentConfig
from core.agents.registry import AgentRegistry
from core.loaders.agent_prompts import load_agent_prompts


@AgentRegistry.register("Resolve", temperature=0.2, max_tokens=200)
def resolve_prompt() -> str:
    return (
        "You are Resolve. Given proposed deltas, validation results, and mode, decide whether to commit now or stage.\n"
        'Return ONLY JSON: {"commit": <true|false>, "reason": <short>, "fixes": <optional obj>}'
    )


def resolve_agent(llm) -> Agent:
    """Legacy function - use AgentRegistry.create_agent('resolve', llm) instead."""
    return AgentRegistry.create_agent('resolve', llm)
