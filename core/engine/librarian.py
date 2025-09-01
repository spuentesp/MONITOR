from __future__ import annotations

from typing import Any


class LibrarianService:
    """Encapsulated retrieval helper that summarizes context for agents.

    It uses the public QueryService; formatting is kept minimal and bounded.
    """

    def __init__(self, query_service: Any):
        self.q = query_service

    def scene_brief(self, scene_id: str, limits: dict[str, int] | None = None) -> str:
        lim = {"rels": 8, "ents": 8, "facts": 6}
        lim.update(limits or {})
        lines: list[str] = [f"Context for scene {scene_id}:"]
        try:
            rels = self.q.relations_effective_in_scene(scene_id)
            if rels:
                lines.append("- Relations:")
                for r in rels[: lim["rels"]]:
                    a = r.get("a") or r.get("A") or r.get("from") or "?"
                    b = r.get("b") or r.get("B") or r.get("to") or "?"
                    t = r.get("type") or r.get("TYPE") or "REL"
                    lines.append(f"  • {a} -[{t}]-> {b}")
        except Exception:
            pass
        try:
            ents = self.q.entities_in_scene(scene_id)
            if ents:
                lines.append("- Participants:")
                for e in ents[: lim["ents"]]:
                    lines.append(f"  • {e.get('id') or e.get('name')}")
        except Exception:
            pass
        try:
            facts = self.q.facts_for_scene(scene_id)
            if facts:
                lines.append("- Facts:")
                for f in facts[: lim["facts"]]:
                    desc = f.get("description") or f.get("text") or "(no description)"
                    lines.append(f"  • {desc[:100]}")
        except Exception:
            pass
        return "\n".join(lines[: 2 + lim["rels"] + lim["ents"] + lim["facts"]])
