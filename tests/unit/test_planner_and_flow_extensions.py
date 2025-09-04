import json

import pytest

from core.agents.planner import planner_agent

pytestmark = pytest.mark.unit

class DummyLLM:
    def chat(self, messages):
        return self._reply(messages)

    def complete(self, system_prompt, messages, temperature, max_tokens):
        return self._reply(messages)

    def _reply(self, messages):
        intent = messages[-1]["content"]
        if "start a new story" in intent:
            return json.dumps([
                {"tool": "bootstrap_story", "args": {"title": "Journey to 800 CE", "time_label": "800 CE", "tags": ["historic"]}, "reason": "initialize story"}
            ])
        if "audit relations" in intent:
            return json.dumps([
                {"tool": "query", "args": {"method": "relations_effective_in_scene", "scene_id": "scene:1"}, "reason": "fetch relations"}
            ])
        if "ingest docs" in intent:
            return json.dumps([
                {"tool": "indexing", "args": {"vector_collection": "kb_u1", "text_index": "kb_u1", "docs": [{"doc_id": "d1", "text": "foo"}]} , "reason": "enable retrieval"}
            ])
        if "search knowledge base" in intent:
            return json.dumps([
                {"tool": "retrieval", "args": {"query": "herb", "vector_collection": "kb_u1", "text_index": "kb_u1", "k": 5}, "reason": "find info"}
            ])
        if "record a fact" in intent:
            return json.dumps([
                {"tool": "recorder", "args": {"scene_id": "scene:1", "facts": [{"description": "Fog is dense."}]}, "reason": "capture observation"}
            ])
        return "[]"

@pytest.mark.parametrize("intent,expected_tool", [
    ("let's start a new story about 800 CE", "bootstrap_story"),
    ("monitor audit relations in this scene", "query"),
    ("ingest docs for this universe", "indexing"),
    ("search knowledge base", "retrieval"),
    ("record a fact about this scene", "recorder"),
])
def test_planner_tools(intent, expected_tool):
    agent = planner_agent(DummyLLM())
    actions = json.loads(agent.act([{"role": "user", "content": intent}]))
    assert isinstance(actions, list)
    assert actions and actions[0]["tool"] == expected_tool
    assert "args" in actions[0]
    assert "reason" in actions[0]

def test_planner_json_only():
    agent = planner_agent(DummyLLM())
    actions = agent.act([{"role": "user", "content": "search knowledge base"}])
    # Should be valid JSON
    parsed = json.loads(actions)
    assert isinstance(parsed, list)
    assert parsed[0]["tool"] == "retrieval"
