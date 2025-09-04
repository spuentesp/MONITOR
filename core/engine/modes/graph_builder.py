"""LangGraph builder for the modes workflow."""
from __future__ import annotations

from typing import Any

from core.engine.tools import ToolContext

from .graph_state import GraphState
from .intent_classifier import classify_intent
from .monitor_node import monitor_node
from .narrator_node import narrator_node


def build_langgraph_modes(tools: ToolContext | None = None) -> Any:
    """Build a LangGraph workflow for narrator/monitor mode routing.
    
    Returns a compiled graph with .invoke(state_dict) -> state_dict method.
    """
    try:
        from langgraph.graph import END, StateGraph
    except Exception:  # pragma: no cover - environment without langgraph
        return _create_sequential_adapter(tools)
    
    return _create_langgraph_adapter(tools)


def _create_sequential_adapter(tools: ToolContext | None) -> Any:
    """Fallback adapter when LangGraph is not available."""
    class _SeqAdapter:
        def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
            s = dict(state)
            if tools is not None:
                s["tools"] = tools  # type: ignore[assignment]
            
            s = classify_intent(s)
            
            if s.get("mode", "narration") == "narration":
                s = narrator_node(s)
            else:
                s = monitor_node(s)
            
            return s
    
    return _SeqAdapter()


def _create_langgraph_adapter(tools: ToolContext | None) -> Any:
    """Create LangGraph-based adapter with fallback."""
    from langgraph.graph import END, StateGraph
    
    class S(dict):
        pass
    
    # Build the graph
    g = StateGraph(S)
    g.add_node("classify", classify_intent)
    g.add_node("narrator", narrator_node)
    g.add_node("monitor", monitor_node)
    g.set_entry_point("classify")
    
    def pick_branch(state: GraphState) -> str:
        mode = state.get("mode", "narration")
        return "narrator" if mode == "narration" else "monitor"
    
    g.add_conditional_edges("classify", pick_branch, {
        "narrator": "narrator", 
        "monitor": "monitor"
    })
    g.add_edge("narrator", END)
    g.add_edge("monitor", END)
    
    compiled = g.compile()
    
    class _Adapter:
        def __init__(self, _compiled):
            self._compiled = _compiled
        
        def invoke(self, inputs: dict[str, Any]) -> dict[str, Any]:
            try:
                # Propagate ToolContext to state
                if tools is not None:
                    inputs = dict(inputs)
                    inputs["tools"] = tools  # type: ignore[index]
                
                out = self._compiled.invoke(inputs)
                if out is not None:
                    return out
                    
            except Exception:
                pass
            
            # Sequential fallback for robustness
            return _create_sequential_adapter(tools).invoke(inputs)
    
    return _Adapter(compiled)
