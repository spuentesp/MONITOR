from __future__ import annotations

from core.agents.base import Agent, AgentConfig


def character_agent(llm, name: str) -> Agent:
	sys = (
		f"You are {name}, a character assistant. Answer in first-person, short lines, "
		"react to events, and keep in-character voice."
	)
	return Agent(AgentConfig(name=f"Personificador:{name}", system_prompt=sys, llm=llm, temperature=0.9, max_tokens=250))

