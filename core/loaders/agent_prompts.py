from __future__ import annotations

from pathlib import Path

import yaml


def load_agent_prompts(path: Path | str = Path("config/agents.yaml")) -> dict[str, str]:
    p = Path(path)
    if not p.exists():
        return {}
    data = yaml.safe_load(p.read_text()) or {}
    out: dict[str, str] = {}
    for k, v in data.items():
        sp = v.get("system_prompt") if isinstance(v, dict) else None
        if sp:
            out[k] = str(sp)
    return out
