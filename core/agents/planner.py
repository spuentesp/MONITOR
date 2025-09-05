from __future__ import annotations

from core.agents.base import Agent
from core.agents.registry import AgentRegistry


@AgentRegistry.register("Planner", temperature=0.1, max_tokens=280)
def planner_prompt():
    """Planner agent prompt."""
    return (
        "You are a planner. Given an intent and compact context, output ONLY a JSON array of actions.\n"
        'Each action: {"tool": <bootstrap_story|query|recorder|narrative|object_upload|indexing|retrieval>, "args": <object>, "reason": <string>}\n'
        "Rules:\n"
        "- Prefer minimal, safe actions.\n"
        "- Use available context placeholders: {scene_id}, {story_id}, {universe_id} if present.\n"
        "- Always produce valid JSON with double quotes. No commentary.\n\n"
        "Examples:\n"
        "1) Start a new story about 800 CE\n"
        '-> [{"tool": "bootstrap_story", "args": {"title": "Journey to 800 CE", "time_label": "800 CE", "tags": ["historic"]}, "reason": "initialize story and opening scene"}]\n\n'
        "2) Audit relations in this scene\n"
        '-> [{"tool": "query", "args": {"method": "relations_effective_in_scene", "scene_id": "{scene_id}"}, "reason": "fetch current relations"}]\n\n'
        "3) Add a short narrator turn to current scene (non-canonical note)\n"
        '-> [{"tool": "narrative", "args": {"op": "insert_turn", "payload": {"text": "The fog thickens.", "role": "narrator", "universe_id": "{universe_id}", "story_id": "{story_id}", "scene_id": "{scene_id}"}}, "reason": "record narrative turn"}]\n\n'
        "4) Ingest two docs for this universe (index only)\n"
        '-> [{"tool": "indexing", "args": {"vector_collection": "kb_{universe_id}", "text_index": "kb_{universe_id}", "docs": [{"doc_id": "d1", "title": "Bestiary", "text": "Griffins and wyverns."}, {"doc_id": "d2", "title": "Herbs", "text": "Kingsfoil heals."}]} , "reason": "enable retrieval"}]\n\n'
        "5) Search knowledge base\n"
        '-> [{"tool": "retrieval", "args": {"query": "healing herb for wounds", "vector_collection": "kb_{universe_id}", "text_index": "kb_{universe_id}", "k": 5}, "reason": "find pertinent info"}]\n\n'
        "6) Record a fact about this scene\n"
        '-> [{"tool": "recorder", "args": {"scene_id": "{scene_id}", "facts": [{"description": "Fog is dense at the docks."}]}, "reason": "capture observation"}]\n'
    )


# Legacy compatibility function
def planner_agent(llm) -> Agent:
    """Legacy compatibility: create planner agent."""
    return AgentRegistry.create_agent("planner", llm)
