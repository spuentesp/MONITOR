from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
import yaml
import json

from core.loaders.yaml_loader import load_omniverse_from_yaml
from core.persistence.neo4j_repo import Neo4jRepo
from core.domain.universe import Universe
from core.domain.story import Story
from core.domain.scene import Scene
from core.domain.entity import ConcreteEntity
from core.domain.sheet import Sheet
from core.domain.axiom import Axiom
from core.domain.system import System
from core.domain.arc import Arc
from core.domain.fact import Fact, RelationState, FactParticipant


class Projector:
    def __init__(self, repo: Neo4jRepo):
        self.repo = repo

    @staticmethod
    def _is_primitive(x):
        return isinstance(x, (str, int, float, bool)) or x is None

    @classmethod
    def _sanitize(cls, value):
        if cls._is_primitive(value):
            return value
        if isinstance(value, list):
            if all(cls._is_primitive(i) for i in value):
                return value
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def project_from_yaml(self, yaml_path: Path | str, ensure_constraints: bool = True) -> None:
        if ensure_constraints:
            self.repo.bootstrap_constraints()

        # Load full domain plus raw YAML for top-level constructs not in domain (e.g., systems)
        omni = load_omniverse_from_yaml(yaml_path)
        raw = yaml.safe_load(Path(yaml_path).read_text())

        # Upsert Omniverse
        self.repo.run(
            "MERGE (o:Omniverse {id:$id}) SET o.name=$name RETURN o",
            id=omni.id,
            name=omni.name,
        )

        # Systems: from YAML top-level (loader doesn't attach to Omniverse)
        systems = raw.get("systems", []) or []
        if systems:
            self._upsert_systems(systems)

        for mv in omni.multiverses:
            self._upsert_multiverse(omni.id, mv.id, mv.name, mv.description)
            # Multiverse-level archetypes and axioms
            if getattr(mv, "archetypes", None):
                self._upsert_archetypes(mv.archetypes)
            if getattr(mv, "axioms", None):
                self._upsert_axioms(mv.axioms)
                # applies_to edges at MV level handled at universe level when universes are created

            for u in mv.universes:
                self._upsert_universe(mv.id, u)

    def _upsert_multiverse(self, omni_id: str, mv_id: str, name: str, description: str | None):
        self.repo.run(
            """
            MERGE (m:Multiverse {id:$id})
            SET m.name=$name, m.description=$description
            WITH m
            MATCH (o:Omniverse {id:$omni_id})
            MERGE (o)-[:HAS]->(m)
            """,
            id=mv_id,
            name=name,
            description=description,
            omni_id=omni_id,
        )

    def _upsert_universe(self, mv_id: str, u: Universe):
        self.repo.run(
            """
            MERGE (u:Universe {id:$id})
            SET u.name=$name, u.description=$description
            WITH u
            MATCH (m:Multiverse {id:$mv_id})
            MERGE (m)-[:HAS_UNIVERSE]->(u)
            """,
            id=u.id,
            name=u.name,
            description=u.description,
            mv_id=mv_id,
        )

        # Axioms & Archetypes at Universe level
        if u.archetypes:
            self._upsert_archetypes(u.archetypes)
        if u.axioms:
            self._upsert_axioms(u.axioms)
            # APPLIES_TO edges
            for ax in u.axioms:
                self._apply_axiom_to_universes(ax)

        # Arcs
        if u.arcs:
            self._upsert_arcs(u.id, u.arcs)

        # Stories & Scenes
        if u.stories:
            self._upsert_stories_and_scenes(u.id, u.stories)

        # Entities & Sheets
        if getattr(u, "entities", None):
            self._upsert_entities_and_sheets(u.id, u.entities)

        # APPEARS_IN from Scene.participants (requires scenes and entities present)
        if u.stories:
            self._upsert_appears_in(u.stories)

        # Facts & Relation States
        if getattr(u, "facts", None):
            self._upsert_facts(u.id, u.facts)
        if getattr(u, "relation_states", None):
            self._upsert_relation_states(u.relation_states)

    def _upsert_archetypes(self, archetypes):
        rows = []
        for a in archetypes:
            props = {
                "name": a.name,
                "description": getattr(a, "description", None),
                "type": getattr(a, "type", None),
                "attributes": getattr(a, "attributes", {}),
                "relations": getattr(a, "relations", {}),
            }
            props = {k: self._sanitize(v) for k, v in props.items()}
            rows.append({"id": a.id, "props": props})
        self.repo.run(
            """
            UNWIND $rows AS row
            MERGE (n:Archetype {id: row.id})
            SET n += row.props
            """,
            rows=rows,
        )

    def _upsert_systems(self, systems: List[Dict[str, Any]]):
        rows = []
        for s in systems:
            props = {k: self._sanitize(v) for k, v in s.items() if k != "id"}
            rows.append({"id": s.get("id"), "props": props})
        if not rows:
            return
        self.repo.run(
            """
            UNWIND $rows AS row
            MERGE (sys:System {id: row.id})
            SET sys += row.props
            """,
            rows=rows,
        )

    def _upsert_axioms(self, axioms: List[Axiom]):
        rows = [
            {
                "id": ax.id,
                "props": {
                    "type": ax.type,
                    "semantics": ax.semantics,
                    "description": ax.description,
                    "probability": ax.probability,
                    "min_count": ax.min_count,
                    "enabled": ax.enabled,
                    "refers_to_archetype": ax.refers_to_archetype,
                },
            }
            for ax in axioms
        ]
        if not rows:
            return
        self.repo.run(
            """
            UNWIND $rows AS row
            MERGE (a:Axiom {id: row.id})
            SET a += row.props
            """,
            rows=rows,
        )
        # REFERS_TO archetype, if present
        self.repo.run(
            """
            UNWIND $rows AS row
            WITH row WHERE row.props.refers_to_archetype IS NOT NULL
            MATCH (a:Axiom {id: row.id})
            MATCH (ar:Archetype {id: row.props.refers_to_archetype})
            MERGE (a)-[:REFERS_TO]->(ar)
            """,
            rows=rows,
        )

    def _apply_axiom_to_universes(self, ax: Axiom):
        if not ax.applies_to:
            return
        self.repo.run(
            """
            UNWIND $ids AS uid
            MATCH (a:Axiom {id:$axid})
            MATCH (u:Universe {id:uid})
            MERGE (a)-[:APPLIES_TO]->(u)
            """,
            ids=ax.applies_to,
            axid=ax.id,
        )

    def _upsert_arcs(self, universe_id: str, arcs: List[Arc]):
        rows = [
            {"id": a.id, "props": {"title": a.title, "tags": getattr(a, "tags", []), "ordering_mode": getattr(a, "ordering_mode", None), "universe_id": universe_id, "story_ids": getattr(a, "story_ids", [])}}
            for a in arcs
        ]
        self.repo.run(
            """
            MATCH (u:Universe {id:$uid})
            UNWIND $rows AS row
            MERGE (a:Arc {id: row.id})
            SET a += row.props
            MERGE (u)-[:HAS_ARC]->(a)
            """,
            uid=universe_id,
            rows=rows,
        )

    def _upsert_stories_and_scenes(self, universe_id: str, stories: List[Story]):
        # Stories
        srows = []
        for s in stories:
            props = {"title": s.title, "summary": s.summary, "universe_id": universe_id, "arc_id": s.arc_id}
            props = {k: self._sanitize(v) for k, v in props.items()}
            srows.append({"id": s.id, "props": props})
        self.repo.run(
            """
            MATCH (u:Universe {id:$uid})
            UNWIND $rows AS row
            MERGE (s:Story {id: row.id})
            SET s += row.props
            MERGE (u)-[:HAS_STORY]->(s)
            """,
            uid=universe_id,
            rows=srows,
        )
        # Arc->Story ordering by input order
        self.repo.run(
            """
            UNWIND $rows AS row
            WITH row WHERE row.props.arc_id IS NOT NULL
            MATCH (a:Arc {id: row.props.arc_id})
            MATCH (s:Story {id: row.id})
            MERGE (a)-[:HAS_STORY {sequence_index: row.seq}]->(s)
            """,
            rows=[{"id": s.id, "props": {"arc_id": s.arc_id}, "seq": idx + 1} for idx, s in enumerate(stories)],
        )
        # Scenes per story
        for s in stories:
            if not s.scenes:
                continue
            scrows = []
            for sc in s.scenes:
                props = {
                    "story_id": s.id,
                    "sequence_index": sc.sequence_index,
                    "when": sc.when,
                    "time_span": sc.time_span,
                    "recorded_at": sc.recorded_at,
                    "location": sc.location,
                }
                props = {k: self._sanitize(v) for k, v in props.items()}
                scrows.append({"id": sc.id, "props": props})
            self.repo.run(
                """
                MATCH (st:Story {id:$sid})
                UNWIND $rows AS row
                MERGE (sc:Scene {id: row.id})
                SET sc += row.props
                MERGE (st)-[:HAS_SCENE {sequence_index: row.props.sequence_index}]->(sc)
                """,
                sid=s.id,
                rows=scrows,
            )

    def _upsert_entities_and_sheets(self, universe_id: str, entities: List[ConcreteEntity]):
        erows = []
        for e in entities:
            props = {"name": e.name, "type": e.type, "attributes": e.attributes, "universe_id": universe_id, "archetype_id": e.archetype_id}
            props = {k: self._sanitize(v) for k, v in props.items()}
            erows.append({"id": e.id, "props": props})
        self.repo.run(
            """
            MATCH (u:Universe {id:$uid})
            UNWIND $rows AS row
            MERGE (e:Entity {id: row.id})
            SET e += row.props
            MERGE (e)-[:BELONGS_TO]->(u)
            """,
            uid=universe_id,
            rows=erows,
        )
        # Sheets
        for e in entities:
            if not e.sheets:
                continue
            shrows = []
            for sh in e.sheets:
                props = {"name": sh.name, "type": sh.type, "attributes": sh.attributes, "story_id": sh.story_id, "system_id": sh.system_id}
                props = {k: self._sanitize(v) for k, v in props.items()}
                shrows.append({"id": sh.id, "props": props, "eid": e.id})
            self.repo.run(
                """
                UNWIND $rows AS row
                MERGE (s:Sheet {id: row.id})
                SET s += row.props
                WITH s, row
                MATCH (e:Entity {id: row.eid})
                MERGE (e)-[hs:HAS_SHEET]->(s)
                SET hs.story_id = row.props.story_id, hs.system_id = row.props.system_id
                """,
                rows=shrows,
            )

        # APPEARS_IN from scene participants (we need participants from YAML; traverse via scenes created earlier)
        # Link scene participants using YAML participants list: they are in YAML; our loader did not attach to domain scenes as edges
        # Create edges using scene data present in DB by matching scene.id and participant ids
        # Note: we'll parse participants by reusing entities list and scene ids already inserted
        # This step is handled in _upsert_facts() where we also create PARTICIPATES_AS; APPEARS_IN are still useful:
        # Build APPEARS_IN from scenes containing participants
        # Since domain Story.Scene includes participants list, we can create edges now.
        # Fetch stories and their scenes from the domain input? We don't have them accessible here; done in _upsert_stories_and_scenes during insert
        # We'll add an extra pass there would complicate. Instead, run a Cypher that scans scenes and a param map of participants.

    def _upsert_appears_in(self, stories: List[Story]):
        rows = []
        for st in stories:
            if not st.scenes:
                continue
            for sc in st.scenes:
                for eid in getattr(sc, "participants", []) or []:
                    rows.append({"scene_id": sc.id, "entity_id": eid})
        if not rows:
            return
        self.repo.run(
            """
            UNWIND $rows AS row
            MATCH (sc:Scene {id: row.scene_id})
            MATCH (e:Entity {id: row.entity_id})
            MERGE (e)-[:APPEARS_IN]->(sc)
            """,
            rows=rows,
        )

    def _upsert_facts(self, universe_id: str, facts: List[Fact]):
        frows = []
        for f in facts:
            props = {
                "universe_id": universe_id,
                "description": f.description,
                "when": f.when,
                "time_span": f.time_span,
                "confidence": f.confidence,
                "derived_from": f.derived_from,
            }
            props = {k: self._sanitize(v) for k, v in props.items()}
            frows.append(
                {
                    "id": f.id,
                    "props": props,
                    "occurs_in": f.occurs_in,
                    "participants": [{"entity_id": p.entity_id, "role": p.role} for p in f.participants],
                }
            )
        if not frows:
            return
        # Upsert facts and OCCURS_IN
        self.repo.run(
            """
            UNWIND $rows AS row
            MERGE (f:Fact {id: row.id})
            SET f += row.props
            WITH row, f
            OPTIONAL MATCH (sc:Scene {id: row.occurs_in})
            FOREACH (_ IN CASE WHEN sc IS NULL THEN [] ELSE [1] END | MERGE (f)-[:OCCURS_IN]->(sc))
            """,
            rows=frows,
        )
        # PARTICIPATES_AS
        self.repo.run(
            """
            UNWIND $rows AS row
            MATCH (f:Fact {id: row.id})
            UNWIND row.participants AS p
            MATCH (e:Entity {id: p.entity_id})
            MERGE (e)-[:PARTICIPATES_AS {role: p.role}]->(f)
            """,
            rows=frows,
        )

    def _upsert_relation_states(self, rels: List[RelationState]):
        rrows = [
            {"id": r.id, "props": {"type": r.type, "started_at": r.started_at, "ended_at": r.ended_at}, "a": r.entity_a, "b": r.entity_b, "set": r.set_in_scene, "chg": r.changed_in_scene, "end": r.ended_in_scene}
            for r in rels
        ]
        if not rrows:
            return
        self.repo.run(
            """
            UNWIND $rows AS row
            MERGE (rs:RelationState {id: row.id})
            SET rs += row.props
            WITH rs, row
            MATCH (a:Entity {id: row.a})
            MATCH (b:Entity {id: row.b})
            MERGE (rs)-[:REL_STATE_FOR {endpoint:'A'}]->(a)
            MERGE (rs)-[:REL_STATE_FOR {endpoint:'B'}]->(b)
            WITH rs, row
            OPTIONAL MATCH (s1:Scene {id: row.set})
            FOREACH (_ IN CASE WHEN s1 IS NULL THEN [] ELSE [1] END | MERGE (rs)-[:SET_IN_SCENE]->(s1))
            WITH rs, row
            OPTIONAL MATCH (s2:Scene {id: row.chg})
            FOREACH (_ IN CASE WHEN s2 IS NULL THEN [] ELSE [1] END | MERGE (rs)-[:CHANGED_IN_SCENE]->(s2))
            WITH rs, row
            OPTIONAL MATCH (s3:Scene {id: row.end})
            FOREACH (_ IN CASE WHEN s3 IS NULL THEN [] ELSE [1] END | MERGE (rs)-[:ENDED_IN_SCENE]->(s3))
            """,
            rows=rrows,
        )
