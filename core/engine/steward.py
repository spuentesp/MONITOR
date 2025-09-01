from __future__ import annotations

from typing import Any

try:
    from core.ports.storage import QueryReadPort  # type: ignore
except Exception:  # pragma: no cover
    QueryReadPort = Any  # type: ignore


class StewardService:
    """Encapsulated continuity checks before commits.

    Returns (ok: bool, warnings: List[str], errors: List[str]).
    """

    def __init__(self, query_service: QueryReadPort | Any):
        self.q = query_service

    def validate(self, deltas: dict[str, Any]) -> tuple[bool, list[str], list[str]]:
        warnings: list[str] = []
        errors: list[str] = []
        scene_id = deltas.get("scene_id")

        # Check that participants referenced in facts exist (if provided)
        facts = deltas.get("facts") or []
        for f in facts:
            parts = f.get("participants") or []
            for p in parts:
                eid = p.get("entity_id") or p.get("id")
                if not eid:
                    warnings.append("Fact participant without entity_id")
                    continue
                try:
                    # Fast existence check via appears-in scene when scene_id is known
                    if scene_id:
                        scene_ents = [e.get("id") for e in self.q.entities_in_scene(scene_id)]
                        if eid not in scene_ents:
                            warnings.append(f"Participant {eid} not in scene {scene_id}")
                except Exception:
                    pass

        # Sanity on relation_states entity ids
        for rs in deltas.get("relation_states") or []:
            a = rs.get("entity_a") or rs.get("a")
            b = rs.get("entity_b") or rs.get("b")
            if not a or not b:
                errors.append("RelationState missing entity_a/entity_b")
            if a == b:
                warnings.append("RelationState with identical endpoints")

        # Basic temporal sanity (if both provided)
        for f in facts:
            ts = f.get("time_span")
            if isinstance(ts, dict):
                start = ts.get("start") or ts.get("from")
                end = ts.get("end") or ts.get("to")
                if start and end and str(start) > str(end):
                    errors.append("Fact time_span start > end")

        ok = len(errors) == 0
        return ok, warnings, errors
