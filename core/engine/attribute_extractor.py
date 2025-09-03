from __future__ import annotations

import re
from typing import Any

_KV_LINE = re.compile(
    r"\b(?P<key>type|class|archetype|species|alias|aka|tags?|traits?|affiliations?|affiliation|faction|stats?)\b\s*[:=]\s*(?P<val>[^;\n\|]+)",
    re.IGNORECASE,
)


def _split_csv(val: str) -> list[str]:
    parts = [p.strip() for p in re.split(r",|;", val) if p.strip()]
    # strip surrounding quotes
    return [re.sub(r"^['\"]|['\"]$", "", p) for p in parts]


def _parse_stats(val: str) -> dict[str, Any]:
    stats: dict[str, Any] = {}
    for tok in re.split(r",|;", val):
        tok = tok.strip()
        m = re.match(r"([A-Za-z][A-Za-z0-9_\- ]*)\s*[:=]\s*([0-9]+)", tok)
        if m:
            k = m.group(1).strip().upper()
            v = int(m.group(2))
            stats[k] = v
    return stats


def distill_entity_attributes(description: str | None) -> dict[str, Any]:
    """Heuristic, deterministic attribute distiller from free text.

    Extracts keys: type, class, archetype, tags (list), traits (list), affiliations (list), stats (dict).
    """
    out: dict[str, Any] = {}
    if not description:
        return out
    # Scan explicit key: value fragments across the whole description
    for m in _KV_LINE.finditer(description):
        key = m.group("key").lower()
        val = m.group("val").strip()
        if key.startswith("tag"):
            out.setdefault("tags", [])
            out["tags"].extend(_split_csv(val))  # type: ignore[index]
            continue
        if key.startswith("trait"):
            out.setdefault("traits", [])
            out["traits"].extend(_split_csv(val))  # type: ignore[index]
            continue
        if key in ("affiliation", "affiliations", "faction"):
            out.setdefault("affiliations", [])
            out["affiliations"].extend(_split_csv(val))  # type: ignore[index]
            continue
        if key in ("alias", "aka"):
            out.setdefault("aliases", [])
            out["aliases"].extend(_split_csv(val))  # type: ignore[index]
            continue
        if key.startswith("stat"):
            stats = _parse_stats(val)
            if stats:
                out["stats"] = {**out.get("stats", {}), **stats}
            continue
        # type/class/archetype take simple token or quoted string
        token = re.match(r"^['\"]([^'\"]+)['\"]$", val)
        out[key] = token.group(1) if token else val
    # Light-weight adjective/known term sweep for traits
    traits = set(map(str.lower, out.get("traits", [])))
    for word in re.findall(
        r"\b(stealthy|gruff|cunning|brave|smart|strong|agile|charismatic|loyal|fearless|ruthless)\b",
        description,
        flags=re.IGNORECASE,
    ):
        traits.add(word.lower())
    if traits:
        out["traits"] = sorted(traits)
    # Deduplicate lists
    for k in ("tags", "affiliations"):
        if k in out:
            out[k] = sorted(set(out[k]))
    return out
