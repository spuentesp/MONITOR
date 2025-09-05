from __future__ import annotations

from core.agents.base import Agent
from core.agents.registry import AgentRegistry


@AgentRegistry.register("IntentRouter", temperature=0.0, max_tokens=8)
def intent_router_prompt():
    """Intent router agent prompt."""
    return (
        "You are an intent router. Classify the user's input into one of: "
        "narrative, monitor, qa, bootstrap, action_examine, action_move, audit_relations. "
        "Return only the label, nothing else."
    )


# Legacy compatibility function
def intent_router_agent(llm) -> Agent:
    """Legacy compatibility: create intent router agent."""
    return AgentRegistry.create_agent("intentrouter", llm)
