from __future__ import annotations

from core.agents.base import Agent
from core.agents.registry import AgentRegistry
from core.utils.constants import MAX_CONTINUITY_TOKENS


@AgentRegistry.register("ContinuityModerator", temperature=0.1, max_tokens=220)
def continuity_prompt():
    """Continuity agent prompt."""
    return (
        "You are Continuity Moderator. Use the provided ontology context (systems/rules, participants, relations, facts)\n"
        "to judge whether the narrator's draft aligns with axioms, limitations, and domain constraints.\n"
        "Respond ONLY with a compact JSON object:\n"
        '{"drift": <bool>, "incorrect": <bool>, "reasons": [<short strings>],\n'
        ' "violations": [{"subject": <\'entity\'|\'relation\'|\'system\'>, "key": <id or rule name>, "reason": <short>}],\n'
        ' "note": <one-line advice>}\n'
        f"Keep it under {MAX_CONTINUITY_TOKENS} tokens. Do not include narrative prose."
    )


# Legacy compatibility function
def continuity_agent(llm) -> Agent:
    """Legacy compatibility: create continuity agent."""
    return AgentRegistry.create_agent("continuitymoderator", llm)
