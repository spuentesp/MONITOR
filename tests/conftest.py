from __future__ import annotations

from pathlib import Path
import sys


def _ensure_repo_root_on_path() -> None:
    # tests/ -> repo root
    root = Path(__file__).resolve().parents[1]
    p = str(root)
    if p not in sys.path:
        sys.path.insert(0, p)


_ensure_repo_root_on_path()
