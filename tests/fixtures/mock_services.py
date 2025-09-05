"""
Mock service implementations for testing.

Provides fake implementations of external services that behave
predictably for testing purposes.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock


class MockQueryService:
    """Mock implementation of query service."""
    
    def __init__(self):
        self.queries: list[dict[str, Any]] = []
        self.results: dict[str, Any] = {}
    
    async def execute(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Mock query execution."""
        self.queries.append({"query": query, "params": params or {}})
        return self.results.get(query, [])
    
    def set_result(self, query: str, result: list[dict[str, Any]]) -> None:
        """Set expected result for a query."""
        self.results[query] = result


class MockNeo4jRepo:
    """Mock Neo4j repository."""
    
    def __init__(self):
        self.executed_queries: list[dict[str, Any]] = []
        self.query_results: dict[str, list[dict[str, Any]]] = {}
    
    async def execute_query(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Mock query execution."""
        self.executed_queries.append({"query": query, "params": params or {}})
        # Return preset result or empty list
        return self.query_results.get(query, [{"id": "test_id"}])
    
    def run(self, query: str, **params) -> list[dict[str, Any]]:
        """Mock synchronous query execution."""
        self.executed_queries.append({"query": query, "params": params})
        return self.query_results.get(query, [])
    
    def set_query_result(self, query: str, result: list[dict[str, Any]]) -> None:
        """Set expected result for a query."""
        self.query_results[query] = result


class MockCacheService:
    """Mock cache service implementation."""
    
    def __init__(self):
        self.cache: dict[str, Any] = {}
    
    async def get(self, key: str) -> Any:
        """Mock cache get."""
        return self.cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Mock cache set."""
        self.cache[key] = value
    
    async def delete(self, key: str) -> bool:
        """Mock cache delete."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False


class MockEmbeddingService:
    """Mock embedding service."""
    
    def __init__(self):
        self.embedded_texts: list[str] = []
    
    async def embed(self, text: str) -> list[float]:
        """Mock text embedding."""
        self.embedded_texts.append(text)
        # Return deterministic embedding based on text hash
        return [float(hash(text) % 100) / 100.0] * 384
    
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Mock batch embedding."""
        return [await self.embed(text) for text in texts]


class MockLLMProvider:
    """Mock LLM provider."""
    
    def __init__(self):
        self.responses: dict[str, str] = {}
        self.default_response = "Mock LLM response"
        self.calls: list[dict[str, Any]] = []
    
    def __call__(self, messages: list[dict[str, Any]], **kwargs) -> str:
        """Mock LLM call."""
        self.calls.append({"messages": messages, "kwargs": kwargs})
        
        # Return preset response for specific prompts or default
        last_message = messages[-1] if messages else {}
        content = last_message.get("content", "")
        return self.responses.get(content, self.default_response)
    
    def set_response(self, prompt: str, response: str) -> None:
        """Set expected response for a specific prompt."""
        self.responses[prompt] = response


class MockStagingStore:
    """Mock staging store for testing."""
    
    def __init__(self):
        self.staged_items: list[dict[str, Any]] = []
    
    def stage(self, deltas: dict[str, Any]) -> None:
        """Mock staging operation."""
        self.staged_items.append(deltas)
    
    def pop(self) -> dict[str, Any] | None:
        """Mock pop operation."""
        return self.staged_items.pop(0) if self.staged_items else None
    
    def peek_all(self) -> list[dict[str, Any]]:
        """Mock peek all operation."""
        return self.staged_items.copy()
    
    def clear(self) -> None:
        """Clear all staged items."""
        self.staged_items.clear()