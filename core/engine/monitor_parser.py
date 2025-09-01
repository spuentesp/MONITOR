from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional


Action = Literal["create_multiverse", "create_universe", "save_fact"]


@dataclass
class MonitorIntent:
    action: Action
    # payload
    multiverse_id: Optional[str] = None
    universe_id: Optional[str] = None
    id: Optional[str] = None  # id to create (universe/multiverse)
    name: Optional[str] = None
    description: Optional[str] = None  # fact description
    scene_id: Optional[str] = None


_RE_QSTR = r'"([^\"]+)"|\'([^\']+)\''

# Common helpers
def _extract_name(text: str) -> Optional[str]:
    # Match either double- or single-quoted name without including quotes in the group result
    m = re.search(rf"(?:nombre|name)\s+(?:\"([^\"]+)\"|'([^']+)' )", text, flags=re.IGNORECASE)
    if not m:
        return None
    return m.group(1) or m.group(2)


def _extract_after(keyword: str, text: str) -> Optional[str]:
    m = re.search(rf"{keyword}\s+(\S+)", text, flags=re.IGNORECASE)
    return m.group(1) if m else None


def _strip_command_prefix(text: str) -> str:
    return re.sub(r"^[\s]*[\/@]?(monitor)\b[:\s]*", "", text, flags=re.IGNORECASE)


def parse_monitor_intent(text: str) -> Optional[MonitorIntent]:
    """Parse simple Monitor commands from free text.

    Supported:
    - crear/crea/create multiverso|multiverse [<id>] [nombre|name "<name>"]
    - crear/crea/create universo|universe [<id>] [nombre|name "<name>"] [multiverso|multiverse <id>]
    - guardar/persistir/save hecho|fact <description> [scene <scene_id>]
    """
    t = text.strip()
    t = _strip_command_prefix(t)
    tl = t.lower()

    # Create multiverse
    if re.search(r"\b(crea(r)?|create)\s+(multiverso|multiverse)\b", tl):
        id_ = _extract_after(r"(?:multiverso|multiverse)", t)
        name = _extract_name(t)
        return MonitorIntent(action="create_multiverse", id=id_, name=name)

    # Create universe
    if re.search(r"\b(crea(r)?|create)\s+(universo|universe)\b", tl):
        id_ = _extract_after(r"(?:universo|universe)", t)
        name = _extract_name(t)
        mv = _extract_after(r"(?:multiverso|multiverse)", t)
        return MonitorIntent(action="create_universe", id=id_, name=name, multiverse_id=mv)

    # Save fact
    if re.search(r"\b(guardar|persistir|save)\s+(hecho|fact)\b", tl):
        # everything after the keyword becomes description; try to capture scene
        # Extract scene first to avoid including it in description
        scene = _extract_after(r"(?:scene|escena)", t)
        desc = re.sub(r"^[\s\S]*?(guardar|persistir|save)\s+(hecho|fact)\s*", "", t, flags=re.IGNORECASE)
        desc = re.sub(r"(?:scene|escena)\s+\S+\s*", "", desc, flags=re.IGNORECASE).strip()
        return MonitorIntent(action="save_fact", description=desc or None, scene_id=scene)

    return None
