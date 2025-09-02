from __future__ import annotations

import os
import sys
from pathlib import Path


def _ensure_repo_root_on_path() -> None:
    # tests/ -> repo root
    root = Path(__file__).resolve().parents[1]
    p = str(root)
    if p not in sys.path:
        sys.path.insert(0, p)


_ensure_repo_root_on_path()
