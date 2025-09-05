"""
Shared utilities for agent orchestration in flows.

This module eliminates duplication of agent calling patterns
across different flow nodes.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def safe_agent_call(
    tools: dict[str, Any], 
    agent_key: str, 
    messages: list[dict[str, Any]], 
    default: Any = None
) -> Any:
    """
    Safe agent invocation with proper error logging.
    
    Args:
        tools: Tools dict containing agents
        agent_key: Key to lookup agent in tools
        messages: Messages to send to agent
        default: Default value if agent fails
    
    Returns:
        Agent response or default value
    """
    try:
        agent = tools[agent_key]
        if agent and callable(agent):
            response = agent(messages)
            return response if response is not None else default
    except Exception as e:
        logger.warning(f"Agent '{agent_key}' failed: {e}")
    return default