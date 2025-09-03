from __future__ import annotations

from core.agents.base import Agent, AgentConfig
from core.loaders.agent_prompts import load_agent_prompts


def continuity_agent(llm) -> Agent:
    prompts = load_agent_prompts()
    sys = prompts.get(
        "continuity",
        (
            "You are Continuity Moderator. Use the provided ontology context (systems/rules, participants, relations, facts)\n"
            "to judge whether the narrator's draft aligns with axioms, limitations, and domain constraints.\n"
            "Respond ONLY with a compact JSON object:\n"
            '{"drift": <bool>, "incorrect": <bool>, "reasons": [<short strings>],\n'
            ' "violations": [{"subject": <\'entity\'|\'relation\'|\'system\'>, "key": <id or rule name>, "reason": <short>}],\n'
            ' "note": <one-line advice>}\n'
            "Keep it under 200 tokens. Do not include narrative prose."
        ),
    )
    # Cooler temperature isn't needed; keep deterministic classification
    return Agent(
        AgentConfig(
            name="ContinuityModerator", system_prompt=sys, llm=llm, temperature=0.1, max_tokens=220
        )
    )
