"""Evidence gathering and context nodes."""
from __future__ import annotations

from typing import Any, Dict

from ..state import FlowState, safe_act, fetch_relations


def librarian(state: FlowState, tools: Dict[str, Any]) -> FlowState:
    """Gather evidence and context for the current operation."""
    scene_id = state.get("scene_id")
    evidence = []
    
    if scene_id:
        rels = fetch_relations(tools, scene_id)
        if rels is not None:
            evidence.append({"relations": rels})
    
    # Optionally let LLM librarian summarize evidence
    if evidence:
        summary = safe_act(
            tools,
            "librarian",
            [{"role": "user", "content": f"Summarize briefly: {str(evidence)[:800]}"}],
            default=None,
        )
        if summary is not None:
            return {**state, "evidence": evidence, "evidence_summary": summary}
    
    return {**state, "evidence": evidence}


def steward(state: FlowState, tools: Dict[str, Any]) -> FlowState:
    """Validate context and provide guidance."""
    # LLM-backed steward for quick validation hints
    hints = safe_act(
        tools,
        "steward",
        [
            {
                "role": "user",
                "content": (
                    f"Validate plan and draft context: "
                    f"{str({k: v for k, v in state.items() if k in ['plan', 'evidence']})[:800]}"
                ),
            }
        ],
        default=None,
    )
    
    if hints is not None:
        return {**state, "validation": {"ok": True, "warnings": [hints]}}
    
    return {**state, "validation": {"ok": True, "warnings": []}}
