"""
Agent Registry for extensible agent registration.

Replaces the copy-paste agent factory pattern with a decorator-based
registration system following the Open/Closed Principle.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from core.agents.base import Agent, AgentConfig
from core.loaders.agent_prompts import load_agent_prompts


@dataclass
class AgentSpec:
    """Specification for an agent registration."""

    name: str
    """Display name of the agent."""

    temperature: float = 0.7
    """LLM temperature setting."""

    max_tokens: int = 300
    """Maximum tokens for agent responses."""

    prompt_key: str | None = None
    """Key to lookup prompt in agent_prompts.yaml (defaults to lowercase name)."""

    fallback_prompt: str | None = None
    """Fallback prompt if not found in yaml."""


class AgentRegistry:
    """
    Extensible registry for agents using decorator pattern.

    Eliminates duplication and allows adding agents without modifying
    existing code, following the Open/Closed Principle.
    """

    _agents: dict[str, tuple[AgentSpec, Callable[[], str]]] = {}
    _prompts_cache: dict[str, str] | None = None

    @classmethod
    def register(
        cls,
        name: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
        prompt_key: str | None = None,
        fallback_prompt: str | None = None,
    ):
        """
        Decorator to register an agent prompt function.

        Args:
            name: Display name of the agent
            temperature: LLM temperature setting
            max_tokens: Maximum tokens for responses
            prompt_key: Key for prompt lookup (defaults to lowercase name)
            fallback_prompt: Fallback if prompt not found

        Example:
            @AgentRegistry.register("Narrator", temperature=0.8, max_tokens=350)
            def narrator_prompt():
                return "You are Narrator, a concise Game Master..."
        """

        def decorator(prompt_func: Callable[[], str]):
            spec = AgentSpec(
                name=name,
                temperature=temperature,
                max_tokens=max_tokens,
                prompt_key=prompt_key or name.lower(),
                fallback_prompt=fallback_prompt,
            )
            cls._agents[name.lower()] = (spec, prompt_func)
            return prompt_func

        return decorator

    @classmethod
    def create_agent(cls, agent_key: str, llm: Any) -> Agent:
        """
        Create an agent by registry key.

        Args:
            agent_key: Registry key (lowercase agent name)
            llm: LLM instance to use

        Returns:
            Configured Agent instance

        Raises:
            KeyError: If agent not registered
        """
        if agent_key not in cls._agents:
            raise KeyError(
                f"Agent '{agent_key}' not registered. Available: {list(cls._agents.keys())}"
            )

        spec, prompt_func = cls._agents[agent_key]

        # Get prompt from YAML or fallback
        if cls._prompts_cache is None:
            cls._prompts_cache = load_agent_prompts()

        system_prompt = (
            cls._prompts_cache.get(spec.prompt_key or spec.name.lower())
            or spec.fallback_prompt
            or prompt_func()
        )

        return Agent(
            AgentConfig(
                name=spec.name,
                system_prompt=system_prompt,
                llm=llm,
                temperature=spec.temperature,
                max_tokens=spec.max_tokens,
            )
        )

    @classmethod
    def build_all_agents(cls, llm: Any) -> dict[str, Agent]:
        """
        Build all registered agents.

        Args:
            llm: LLM instance to use

        Returns:
            Dictionary mapping agent keys to Agent instances
        """
        return {key: cls.create_agent(key, llm) for key in cls._agents.keys()}

    @classmethod
    def list_registered(cls) -> list[str]:
        """List all registered agent keys."""
        return list(cls._agents.keys())

    @classmethod
    def clear_registry(cls) -> None:
        """Clear registry (mainly for testing)."""
        cls._agents.clear()
        cls._prompts_cache = None
