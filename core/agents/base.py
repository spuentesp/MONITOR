from __future__ import annotations

from dataclasses import dataclass, field

from core.generation.interfaces.llm import LLM, Message


@dataclass
class AgentConfig:
    name: str
    system_prompt: str
    llm: LLM
    temperature: float = 0.7
    max_tokens: int = 400


class Agent:
    def __init__(self, config: AgentConfig):
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    def act(self, messages: list[Message]) -> str:
        return self.config.llm.complete(
            system_prompt=self.config.system_prompt,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )


@dataclass
class Session:
    """A simple in-memory multi-agent session; routes turns to a primary agent.

    This is intentionally minimal to allow offline tests and fast iteration.
    """

    primary: Agent
    history: list[Message] = field(default_factory=list)

    def user(self, content: str) -> None:
        self.history.append({"role": "user", "content": content})

    def system(self, content: str) -> None:
        self.history.append({"role": "system", "content": content})

    def step(self) -> str:
        reply = self.primary.act(self.history)
        self.history.append({"role": "assistant", "content": reply})
        return reply
