"""
Flow builder and registry for LangGraph flows.

This module contains the main flow construction logic and
provides the public interface for building and selecting flows.
"""

from __future__ import annotations

import json
import os
from typing import Any

from core.engine.resolve_tool import resolve_commit_tool
from core.utils.env import env_bool, env_str
from core.utils.persist import truncate_fact_description
from core.engine.flow_utils import tool_schema as flow_tool_schema, ops_prelude as flow_ops_prelude

from .graph_builder import build_langgraph_flow, create_fallback_execution


# Persona and verbosity toggles via env
def _flag_bool(name: str, default: bool = False) -> bool:
    return env_bool(name, default)

MONITOR_VERBOSE_TASKS = _flag_bool("MONITOR_VERBOSE_TASKS", True)
MONITOR_PERSONA = env_str("MONITOR_PERSONA", "guardian") or "guardian"

def _ops_prelude(actions: list[dict[str, Any]]) -> str | None:
    return flow_ops_prelude(actions, persona=MONITOR_PERSONA, verbose=MONITOR_VERBOSE_TASKS)


def _env_flag(name: str, default: str = "0") -> bool:
    """Parse common boolean-ish env flags once using shared util."""
    return env_bool(name, default in ("1", "true", "True"))


def select_engine_backend() -> str:
    """Return 'langgraph' by default; allow explicit override via env."""
    val = (env_str("MONITOR_ENGINE_BACKEND", "langgraph", lower=True) or "langgraph")
    return "langgraph" if val in ("langgraph", "lg") else "inmemory"


class FlowAdapter:
    """Adapter for compiled LangGraph flows with fallback execution."""
    
    def __init__(self, compiled_graph):
        self._compiled = compiled_graph

    def invoke(self, inputs: dict[str, Any]) -> dict[str, Any]:
        try:
            out = self._compiled.invoke(inputs)
            if out is not None:
                return out
        except Exception:
            pass
        
        # Fallback: sequential execution to produce a final state dict
        return create_fallback_execution(inputs)


# Re-export the main build function
build_flow = build_langgraph_flow
