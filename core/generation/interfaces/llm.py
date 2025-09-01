from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


Message = Dict[str, str]  # {"role": "user|assistant|system", "content": str}


class LLM(ABC):
    @abstractmethod
    def complete(
        self,
        *,
        system_prompt: str,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 400,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:  # returns assistant text
        raise NotImplementedError


@dataclass
class CompletionConfig:
    temperature: float = 0.7
    max_tokens: int = 400
    extra: Optional[Dict[str, Any]] = None
