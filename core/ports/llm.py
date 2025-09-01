from __future__ import annotations

from typing import Any, Protocol, TypedDict


class Message(TypedDict):
    role: str
    content: str


class LLMPort(Protocol):
    def complete(
        self,
        *,
        system_prompt: str,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 400,
        extra: dict[str, Any] | None = None,
    ) -> str: ...
