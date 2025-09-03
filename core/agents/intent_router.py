from __future__ import annotations

from core.agents.base import Agent, AgentConfig


def intent_router_agent(llm) -> Agent:
    system = (
        "You are an intent router. Classify the user's input into one of: "
        "narrative, monitor, qa, bootstrap, action_examine, action_move, audit_relations. "
        "Return only the label, nothing else."
    )
    return Agent(
        AgentConfig(
            name="IntentRouter", system_prompt=system, llm=llm, temperature=0.0, max_tokens=8
        )
    )
