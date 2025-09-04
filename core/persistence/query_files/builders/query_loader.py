from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class QueryLoader:
    """Loads and caches Cypher queries from .cypher files."""
    
    def __init__(self, queries_dir: str | Path | None = None):
        if queries_dir is None:
            # Default to cypher directory relative to this file
            queries_dir = Path(__file__).parent.parent / "cypher"
        self.queries_dir = Path(queries_dir)
        self._cache: dict[str, str] = {}
    
    def load(self, query_name: str) -> str:
        """Load a query by name (without .cypher extension)."""
        if query_name in self._cache:
            return self._cache[query_name]
        
        query_path = self.queries_dir / f"{query_name}.cypher"
        if not query_path.exists():
            raise FileNotFoundError(f"Query file not found: {query_path}")
        
        with open(query_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        self._cache[query_name] = content
        return content
    
    def available_queries(self) -> list[str]:
        """List all available query names."""
        if not self.queries_dir.exists():
            return []
        return [
            f.stem for f in self.queries_dir.glob("*.cypher")
            if f.is_file()
        ]


# Global instance for convenience
_default_loader = QueryLoader()


def load_query(name: str) -> str:
    """Load a query using the default loader."""
    return _default_loader.load(name)


def list_queries() -> list[str]:
    """List available queries using the default loader."""
    return _default_loader.available_queries()
