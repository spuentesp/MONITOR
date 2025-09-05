from __future__ import annotations

from core.agents.base import Agent
from core.agents.registry import AgentRegistry


@AgentRegistry.register("QA", temperature=0.0, max_tokens=64)
def qa_prompt():
    """QA agent prompt."""
    return "You answer in one short line using only: Yes, No, or Unsure, followed by a very brief rationale."


# Legacy compatibility function
def qa_agent(llm) -> Agent:
    """Legacy compatibility: create QA agent."""
    return AgentRegistry.create_agent("qa", llm)
