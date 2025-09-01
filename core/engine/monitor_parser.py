from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional


Action = Literal[
    "create_multiverse",
    "create_universe",
    "save_fact",
    "setup_universe",
    # GM-aid read intents
    "list_multiverses",
    "list_universes",
    "list_stories",
    "show_entity_info",
    "list_enemies",
    "last_seen",
]


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
    entity_name: Optional[str] = None
    role: Optional[str] = None


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
    - list/show multiverses
    - list/show universes [multiverse <id>]
    - list/show stories [universe <id>]
    - show/info/tell me about <entity_name> [in universe <id>]
    - list enemies of <entity_name> [in universe <id>] (MVP: role-based list)
    - last time they saw <entity_name> [in universe <id>]
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

    # Setup universe (wizard)
    if re.search(r"\b(iniciar|configurar|setup|start|nuevo|nueva)\s+(universo|universe)\b", tl):
        id_ = _extract_after(r"(?:universo|universe)", t)
        name = _extract_name(t)
        mv = _extract_after(r"(?:multiverso|multiverse)", t)
        return MonitorIntent(action="setup_universe", id=id_, name=name, multiverse_id=mv)
    # Save fact
    if re.search(r"\b(guardar|persistir|save)\s+(hecho|fact)\b", tl):
        # everything after the keyword becomes description; try to capture scene
        # Extract scene first to avoid including it in description
        scene = _extract_after(r"(?:scene|escena)", t)
        desc = re.sub(r"^[\s\S]*?(guardar|persistir|save)\s+(hecho|fact)\s*", "", t, flags=re.IGNORECASE)
        desc = re.sub(r"(?:scene|escena)\s+\S+\s*", "", desc, flags=re.IGNORECASE).strip()
        return MonitorIntent(action="save_fact", description=desc or None, scene_id=scene)

    # List multiverses
    if re.search(r"\b(list|show)\s+(multiverses|multiversos)\b", tl):
        return MonitorIntent(action="list_multiverses")

    # List universes (optionally within multiverse)
    if re.search(r"\b(list|show)\s+(universes|universos)\b", tl):
        mv = _extract_after(r"(?:multiverso|multiverse)", t)
        return MonitorIntent(action="list_universes", multiverse_id=mv)

    # List stories (optionally within universe)
    if re.search(r"\b(list|show)\s+(stories|historias|arcs)\b", tl):
        u = _extract_after(r"(?:universo|universe)", t)
        return MonitorIntent(action="list_stories", universe_id=u)

    # Show entity info by name within a universe
    if re.search(r"\b(show|info|who\s+is|tell\s+me\s+about)\b", tl):
        # capture quoted or unquoted name chunk before optional 'in universe'
        m = re.search(rf"(show|info|who\\s+is|tell\\s+me\\s+about)\s+({_RE_QSTR}|[A-Za-z0-9_\- ]+)", t, flags=re.IGNORECASE)
        if m:
            raw = m.group(2)
            name = None
            if raw:
                qq = re.match(rf"{_RE_QSTR}", raw)
                if qq:
                    name = qq.group(1) or qq.group(2)
                else:
                    name = raw.strip()
            u = _extract_after(r"(?:universo|universe)", t)
            return MonitorIntent(action="show_entity_info", entity_name=name, universe_id=u)

    # List enemies of <name>
    if re.search(r"\b(enemies\s+of|enemigos\s+de)\b", tl):
        m = re.search(r"(?:enemies\s+of|enemigos\s+de)\s+([^,]+)", t, flags=re.IGNORECASE)
        name = m.group(1).strip() if m else None
        u = _extract_after(r"(?:universo|universe)", t)
        return MonitorIntent(action="list_enemies", entity_name=name, universe_id=u)

    # Last time they saw <name>
    if re.search(r"\blast\s+time\s+(they\s+)?saw\b", tl) or re.search(r"\bultima\s+vez\s+que\s+(lo|la|les)\s+vieron\b", tl):
        m = re.search(r"(?:saw|vieron)\s+([^,]+)$", t, flags=re.IGNORECASE)
        name = m.group(1).strip() if m else None
        u = _extract_after(r"(?:universo|universe)", t)
        return MonitorIntent(action="last_seen", entity_name=name, universe_id=u)

    return None
