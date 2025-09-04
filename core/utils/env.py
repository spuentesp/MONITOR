from __future__ import annotations

import os


def env_bool(name: str, default: bool = False) -> bool:
    """Return a boolean flag from env.

    Truthy values: 1, true, True. Everything else is false.
    """
    raw = os.getenv(name)
    if raw is None:
        return bool(default)
    return raw in ("1", "true", "True")


def env_str(name: str, default: str | None = None, *, lower: bool = False) -> str | None:
    """Return a string from env; optionally lowercase the value.
    Returns default if unset.
    """
    val = os.getenv(name, default if default is not None else None)
    if val is None:
        return None
    return val.lower() if lower else val


def env_float(name: str, default: float) -> float:
    """Return a float from env or default if missing/invalid."""
    raw = os.getenv(name)
    if raw is None:
        return float(default)
    try:
        return float(raw)
    except Exception:
        return float(default)
