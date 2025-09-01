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
    # Write intents
    "add_scene",
    "modify_last_scene",
    "retcon_entity",
    # Seeding entities
    "seed_pcs",
    "seed_npcs",
    "create_entity",
    "start_story",
    "save_conversation",
    "show_conversation",
    "end_scene",
]


@dataclass
class MonitorIntent:
    action: Action
    # payload
    multiverse_id: Optional[str] = None
    universe_id: Optional[str] = None
    story_id: Optional[str] = None
    id: Optional[str] = None  # id to create (universe/multiverse)
    name: Optional[str] = None
    description: Optional[str] = None  # fact description
    scene_id: Optional[str] = None
    entity_name: Optional[str] = None
    role: Optional[str] = None
    participants: Optional[list[str]] = None
    replacement_name: Optional[str] = None
    names: Optional[list[str]] = None
    kind: Optional[str] = None  # PC or NPC
    entity_type: Optional[str] = None  # domain-specific type/class
    topics: Optional[list[str]] = None
    interests: Optional[list[str]] = None
    system_id: Optional[str] = None


_RE_QSTR = r'"([^\"]+)"|\'([^\']+)\''

# Common helpers
def _extract_name(text: str) -> Optional[str]:
    # Match either double- or single-quoted name without including quotes in the group result
    m = re.search(rf"(?:nombre|name)\s+(?:\"([^\"]+)\"|'([^']+)')", text, flags=re.IGNORECASE)
    if not m:
        return None
    return m.group(1) or m.group(2)


def _extract_after(keyword: str, text: str) -> Optional[str]:
    m = re.search(rf"{keyword}\s+(\S+)", text, flags=re.IGNORECASE)
    return m.group(1) if m else None


def _strip_command_prefix(text: str) -> str:
    return re.sub(r"^[\s]*[\/@]?(monitor)\b[:\s]*", "", text, flags=re.IGNORECASE)


def _extract_name_list(text: str) -> list[str]:
    # Find sequences after seed pcs/npcs or similar markers; collect quoted or comma-separated names
    # This is best-effort: look for quoted strings anywhere, else fallback to comma-separated words after the verb
    names: list[str] = []
    # Prefer quoted strings
    for m in re.finditer(_RE_QSTR, text):
        nm = m.group(1) or m.group(2)
        if nm:
            names.append(nm.strip())
    if names:
        return names
    # Fallback: capture after the keyword, split by comma
    m = re.search(r"\b(seed|crear|create|agregar|add)\b[\s\S]*?\b(pcs|players|npcs|pnjs|characters|personajes)\b\s+(.+)$", text, flags=re.IGNORECASE)
    if m:
        tail = m.group(3)
        for part in tail.split(","):
            nm = part.strip()
            if nm:
                names.append(re.sub(r"^['\"]|['\"]$", "", nm))
    return names


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
    - add scene [name "..."] [story <id>] [participants "A", "B"] [with "<description>"]
    - modify last scene [with "<description>"] [participants "A", "B"]
    - retcon <name> [to <replacement>]
    - seed pcs "A", "B" | seed npcs "Goon", "Sniper"
    - create entity/character "Name" [as pc|npc] [type "mutant"]
    - start a new story [system <id>] [topics "...", ...] [interests "...", ...] [name "Universe" story "Title"]
    - save conversation log
    - show conversation | show transcript
    - end scene | terminar escena
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

    # Add scene
    if re.search(r"\b(add|create)\s+(a\s+)?scene\b", tl) or re.search(r"\bagregar\s+(una\s+)?escena\b", tl):
        name = _extract_name(t)
        story = _extract_after(r"(?:story|historia)", t)
        # participants: quoted names after 'participants' or 'with'
        parts: list[str] = []
        for m in re.finditer(r"(?:participants|con|including|incluyendo)\s+((?:\"[^\"]+\"|'[^']+'|[^,]+)(?:\s*,\s*(?:\"[^\"]+\"|'[^']+'|[^,]+))*)", t, flags=re.IGNORECASE):
            chunk = m.group(1)
            for p in re.findall(rf"{_RE_QSTR}|([^,]+)", chunk):
                if isinstance(p, tuple):
                    # when using findall with groups, we get tuples; flatten
                    q1, q2, plain = p
                    candidate = (q1 or q2 or plain).strip()
                else:
                    candidate = str(p).strip()
                if candidate:
                    # strip surrounding quotes if any
                    candidate = re.sub(r"^['\"]|['\"]$", "", candidate)
                    parts.append(candidate)
        # description after 'with'
        m = re.search(r"\bwith\b\s+(.*)$", t, flags=re.IGNORECASE)
        desc = m.group(1).strip() if m else None
        return MonitorIntent(action="add_scene", name=name, story_id=story, participants=(parts or None), description=desc)

    # Modify last scene
    if re.search(r"\b(modify|update|append)\s+(the\s+)?last\s+scene\b", tl) or re.search(r"\bmodificar\s+(la\s+)?ultima\s+escena\b", tl):
        # capture description after the phrase
        desc = re.sub(r"^[\s\S]*?(modify|update|append)\s+(the\s+)?last\s+scene\s*", "", t, flags=re.IGNORECASE).strip()
        # optional participants list
        parts: list[str] = []
        for m in re.finditer(r"(?:participants|con|including|incluyendo)\s+((?:\"[^\"]+\"|'[^']+'|[^,]+)(?:\s*,\s*(?:\"[^\"]+\"|'[^']+'|[^,]+))*)", t, flags=re.IGNORECASE):
            chunk = m.group(1)
            for p in re.findall(rf"{_RE_QSTR}|([^,]+)", chunk):
                if isinstance(p, tuple):
                    q1, q2, plain = p
                    candidate = (q1 or q2 or plain).strip()
                else:
                    candidate = str(p).strip()
                if candidate:
                    candidate = re.sub(r"^['\"]|['\"]$", "", candidate)
                    parts.append(candidate)
        return MonitorIntent(action="modify_last_scene", description=(desc or None), participants=(parts or None))

    # Retcon entity
    if re.search(r"\bretcon\b", tl):
        m = re.search(r"retcon\s+([^\s].*?)\s*(?:to\s+([^\s].*))?$", t, flags=re.IGNORECASE)
        name = m.group(1).strip() if m else None
        replacement = m.group(2).strip() if (m and m.lastindex and m.lastindex >= 2 and m.group(2)) else None
        return MonitorIntent(action="retcon_entity", entity_name=name, replacement_name=replacement)

    # Start a new story (GM onboarding)
    if re.search(r"\bstart\s+(a\s+)?new\s+story\b", tl) or re.search(r"\biniciar\s+(una\s+)?nueva\s+historia\b", tl):
        topics = _extract_name_list(t)
        interests_match = re.search(r"interests?\s+(.+)$", t, flags=re.IGNORECASE)
        interests = _extract_name_list(interests_match.group(1)) if interests_match else None
        system_id = _extract_after(r"(?:system|sistema)", t)
        uni_name = None
        m_un = re.search(r"\buniverse\s+('([^']+)'|\"([^\"]+)\")", t, flags=re.IGNORECASE)
        if m_un:
            uni_name = (m_un.group(2) or m_un.group(3))
        story_name = None
        m_st = re.search(r"\bstory\s+('([^']+)'|\"([^\"]+)\")", t, flags=re.IGNORECASE)
        if m_st:
            story_name = (m_st.group(2) or m_st.group(3))
        return MonitorIntent(action="start_story", topics=(topics or None), interests=interests, system_id=system_id, name=uni_name, description=story_name)

    # Seed PCs
    if re.search(r"\bseed\s+(pcs|players)\b", tl) or re.search(r"\bsembrar\s+(pj|pjs)\b", tl):
        names = _extract_name_list(t)
        return MonitorIntent(action="seed_pcs", names=(names or None), kind="PC")

    # Seed NPCs
    if re.search(r"\bseed\s+(npcs|pnjs)\b", tl):
        names = _extract_name_list(t)
        return MonitorIntent(action="seed_npcs", names=(names or None), kind="NPC")

    # Create single entity/character
    if re.search(r"\b(create|add|crear|agregar)\s+(entity|character|personaje)\b", tl):
        name = _extract_name(t)
        kind = None
        if re.search(r"\bas\s+pc\b", tl) or re.search(r"\bcomo\s+pj\b", tl):
            kind = "PC"
        if re.search(r"\bas\s+npc\b", tl) or re.search(r"\bcomo\s+pnj\b", tl):
            kind = "NPC"
        etype = _extract_after(r"(?:type|tipo)", t)
        if etype and re.match(r"^['\"]", etype):
            etype = re.sub(r"^['\"]|['\"]$", "", etype)
        # Optional description for attribute distillation
        m_desc = re.search(r"\bwith\b\s+('([^']+)'|\"([^\"]+)\"|(.+))$", t, flags=re.IGNORECASE)
        desc = None
        if m_desc:
            desc = (m_desc.group(2) or m_desc.group(3) or m_desc.group(4) or "").strip()
        # Optional assignment to story/scene
        story = _extract_after(r"(?:story|historia)", t)
        scene = _extract_after(r"(?:scene|escena)", t)
        # Fallback: name right after keyword character/entity
        if not name:
            m2 = re.search(r"(?:entity|character|personaje)\s+(?:\"([^\"]+)\"|'([^']+)')", t, flags=re.IGNORECASE)
            if m2:
                name = m2.group(1) or m2.group(2)
        return MonitorIntent(action="create_entity", name=name, kind=kind, entity_type=etype, description=desc, story_id=story, scene_id=scene)

    # Save conversation
    if re.search(r"\bsave\s+(the\s+)?conversation\b", tl):
        return MonitorIntent(action="save_conversation")

    # Show conversation / transcript
    if re.search(r"\b(show|mostrar)\s+(conversation|transcript|conversación)\b", tl):
        return MonitorIntent(action="show_conversation")

    # End scene
    if re.search(r"\b(end|finish|close)\s+(the\s+)?scene\b", tl) or re.search(r"\b(terminar|cerrar)\s+(la\s+)?escena\b", tl):
        return MonitorIntent(action="end_scene")

    return None
