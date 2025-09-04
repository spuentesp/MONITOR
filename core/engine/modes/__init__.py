"""Modular LangGraph modes for narrator/monitor conversation flow.

This package splits the original monolithic langgraph_modes.py into focused modules:

- graph_state: State management and utilities
- constants: Regex patterns and help text
- intent_classifier: Mode classification logic
- narrator_node: Creative storytelling responses
- monitor_node: Operational commands and system management
- wizard_flows: Multi-turn setup wizards
- monitor_actions: Core data operations
- graph_builder: LangGraph construction

This modular approach follows Single Responsibility Principle and makes
the codebase more maintainable and testable.
"""

from .graph_builder import build_langgraph_modes
from .graph_state import GraphState, Mode

__all__ = ["build_langgraph_modes", "GraphState", "Mode"]
