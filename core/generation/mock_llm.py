from __future__ import annotations

from typing import List, Dict, Any, Optional

from core.generation.interfaces.llm import LLM, Message


class MockLLM(LLM):
    """A very simple LLM stub for tests and local demos.

    It echoes a compact response influenced by the last user message.
    """

    def complete(
        self,
        *,
        system_prompt: str,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 400,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "" )
        last_user = last_user.strip().split("\n")[0][:120]
        if "Archivista" in system_prompt:
            return f"- Summary: {last_user or 'No events yet.'}\n- Threads: [tbd]"
        if "Narrador" in system_prompt:
            return f"The scene unfolds: {last_user or 'A quiet start.'} What do you do?"
        return f"[{system_prompt.split(',')[0]}] {last_user or 'Ready.'}"
