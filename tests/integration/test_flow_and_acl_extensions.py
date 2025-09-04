import json
from typing import Any

from fastapi.testclient import TestClient
import pytest

from core.engine.context import ContextToken
from core.engine.langgraph_flow import build_langgraph_flow
from core.engine.tools import ToolContext
from core.engine.tools import recorder_tool as real_recorder_tool
from core.interfaces.api_interface import app

pytestmark = pytest.mark.integration

# --- ACL tests ---

def _ctx_header(mode: str = "read") -> dict[str, str]:
    tok = ContextToken(omniverse_id="o1", multiverse_id="m1", universe_id="u1", mode=mode)
    return {"X-Context-Token": tok.model_dump_json()}


def test_modes_chat_autopilot_requires_write_token():
    client = TestClient(app)
    body = {
        "session_id": "s1",
        "message": "hello",
        "mode": "autopilot",
    }
    r = client.post("/api/langgraph/modes/chat", json=body, headers=_ctx_header(mode="read"))
    assert r.status_code == 403
    assert "require" in r.text.lower()


# --- recorder DTO validation tests ---

def test_recorder_dto_validation_error_on_bad_participants():
    ctx = ToolContext(query_service=None, dry_run=True)
    bad = {
        "scene_id": "scene:1",
        "facts": [
            {"description": "bad participants shape", "participants": "not-a-list"}
        ],
    }
    res = real_recorder_tool(ctx, draft="x", deltas=bad)
    assert res.get("mode") == "error"


def test_recorder_dto_valid_dry_run():
    ctx = ToolContext(query_service=None, dry_run=True)
    good = {"scene_id": "scene:1", "facts": [{"description": "ok"}]}
    res = real_recorder_tool(ctx, draft="x", deltas=good)
    assert res.get("mode") == "dry_run"
    assert res.get("deltas", {}).get("facts")


# --- Flow tests for indexing/retrieval actions ---

class DummyPlanner:
    def act(self, messages: list[dict[str, str]]) -> str:
        content = messages[-1]["content"]
        if "ingest" in content:
            return json.dumps([
                {
                    "tool": "indexing",
                    "args": {
                        "vector_collection": "kb_u1",
                        "text_index": "kb_u1",
                        "docs": [{"doc_id": "d1", "text": "foo"}],
                    },
                    "reason": "enable retrieval",
                },
                {
                    "tool": "retrieval",
                    "args": {
                        "query": "foo",
                        "vector_collection": "kb_u1",
                        "text_index": "kb_u1",
                        "k": 3,
                    },
                    "reason": "search",
                },
            ])
        return "[]"


class DummyLLM:
    def complete(self, system_prompt: str, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
        return "[]"


class Ctx:
    def __init__(self):
        self.dry_run = True
        self.log: list[dict[str, Any]] = []


def test_flow_executes_indexing_and_retrieval_actions():
    ctx = Ctx()

    def indexing_tool(_ctx, *, llm=None, vector_collection, text_index, docs):
        _ctx.log.append({"op": "index", "vc": vector_collection, "ti": text_index, "docs": docs})
        return {"ok": True, "mode": "commit", "result": {"indexed": {"vectors": len(docs), "texts": len(docs)}}}

    def retrieval_tool(_ctx, *, query, vector_collection, text_index, k=8, filter_terms=None):
        _ctx.log.append({"op": "search", "q": query, "vc": vector_collection, "ti": text_index})
        return {"ok": True, "results": [{"doc_id": "d1", "score": 1.0}]}

    def query_tool(_ctx, method: str, **kwargs):
        return []

    tools_pkg = {
        "ctx": ctx,
        "llm": DummyLLM(),
        "planner": DummyPlanner(),
        "query_tool": query_tool,
        "recorder_tool": lambda _ctx, **kw: {"mode": "dry_run", "deltas": kw.get("deltas", {})},
        "bootstrap_story_tool": lambda _ctx, **kw: {"refs": {"scene_id": "scene:x", "universe_id": "u1", "story_id": "st1"}},
        "narrative_tool": lambda *_a, **_k: {"ok": True, "mode": "dry_run"},
        "indexing_tool": indexing_tool,
        "retrieval_tool": retrieval_tool,
        "object_upload_tool": lambda *_a, **_k: {"ok": True, "mode": "dry_run"},
        # Provide no-op agents for others; flow falls back safely
        "narrator": None,
        "archivist": None,
        "director": None,
        "librarian": None,
        "steward": None,
        "critic": None,
        "intent_router": None,
        "qa": None,
        "continuity": None,
        "conductor": None,
    }

    graph = build_langgraph_flow(tools_pkg)
    out = graph.invoke({"intent": "please ingest and then search", "universe_id": "u1"})

    results = out.get("action_results", [])
    assert any(r.get("tool") == "indexing" for r in results)
    assert any(r.get("tool") == "retrieval" for r in results)
    assert ctx.log and ctx.log[0]["op"] == "index"
    assert ctx.log[1]["op"] == "search"


def test_flow_injects_citations_into_narrative_and_sets_narrative_result():
    ctx = Ctx()

    def retrieval_tool(_ctx, *, query, vector_collection, text_index, k=8, filter_terms=None):
        return {
            "ok": True,
            "results": [
                {"doc_id": "d1", "score": 0.9, "text": "alpha"},
                {"doc_id": "d2", "score": 0.8, "text": "beta"},
            ],
        }

    captured_payloads: list[dict[str, Any]] = []

    def narrative_tool(_ctx, op: str, *, llm=None, **payload):
        captured_payloads.append(payload)
        return {"ok": True, "mode": "dry_run", "echo": payload}

    class Planner:
        def act(self, _msgs):
            return json.dumps([
                {"tool": "retrieval", "args": {"query": "q", "vector_collection": "kb", "text_index": "kb"}},
                {"tool": "narrative", "args": {"op": "continue", "payload": {"text": "go"}}},
            ])

    tools_pkg = {
        "ctx": ctx,
        "llm": DummyLLM(),
        "planner": Planner(),
        "query_tool": lambda *_a, **_k: [],
        "recorder_tool": lambda *_a, **_k: {"mode": "dry_run"},
        "bootstrap_story_tool": lambda *_a, **_k: {"refs": {"scene_id": "s", "universe_id": "u", "story_id": "st"}},
        "narrative_tool": narrative_tool,
        "indexing_tool": lambda *_a, **_k: {"ok": True, "mode": "dry_run"},
        "retrieval_tool": retrieval_tool,
        "object_upload_tool": lambda *_a, **_k: {"ok": True, "mode": "dry_run"},
        # unused agents
        "narrator": None,
        "archivist": None,
        "director": None,
        "librarian": None,
        "steward": None,
        "critic": None,
        "intent_router": None,
        "qa": None,
        "continuity": None,
        "conductor": None,
    }

    graph = build_langgraph_flow(tools_pkg)
    out = graph.invoke({"intent": "tell me something", "universe_id": "u"})

    assert "narrative_result" in out
    assert captured_payloads, "narrative_tool should have been called"
    meta = captured_payloads[-1].get("meta")
    assert meta and isinstance(meta.get("citations"), list) and len(meta["citations"]) == 2
