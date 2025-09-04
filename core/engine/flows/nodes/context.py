"""Evidence gathering and context nodes."""

from __future__ import annotations

from typing import Any

from ..state import FlowState, fetch_relations, safe_act


def librarian(state: FlowState, tools: dict[str, Any]) -> FlowState:
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
            return FlowState({**state, "evidence": evidence, "evidence_summary": summary})

    return FlowState({**state, "evidence": evidence})


def steward(state: FlowState, tools: dict[str, Any]) -> FlowState:
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
        return FlowState({**state, "validation": {"ok": True, "warnings": [hints]}})

    return FlowState({**state, "validation": {"ok": True, "warnings": []}})
