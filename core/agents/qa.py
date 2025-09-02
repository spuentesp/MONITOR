from __future__ import annotations

from core.agents.base import Agent, AgentConfig


def qa_agent(llm) -> Agent:
    system = (
        "You answer in one short line using only: Yes, No, or Unsure, followed by a very brief rationale."
    )
    return Agent(AgentConfig(name="QA", system_prompt=system, llm=llm, temperature=0.0, max_tokens=64))
