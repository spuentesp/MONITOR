from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from core.domain.arc import Arc
from core.domain.axiom import Axiom
from core.domain.entity import ArchetypeEntity, ConcreteEntity
from core.domain.event import Event
from core.domain.fact import Fact, FactParticipant, RelationState
from core.domain.multiverse import Multiverse
from core.domain.omniverse import Omniverse
from core.domain.scene import Scene
from core.domain.sheet import Sheet
from core.domain.story import Story
from core.domain.system import System
from core.domain.universe import Universe


def _load_systems(doc: dict[str, Any]) -> dict[str, System]:
    systems = {}
    for s in doc.get("systems", []):
        systems[s["id"]] = System(**s)
    return systems


def load_omniverse_from_yaml(path: Path | str) -> Omniverse:
    data = yaml.safe_load(Path(path).read_text())
    omni_dict = data["omniverse"]

    _load_systems(data)

    multiverses: list[Multiverse] = []
    for mv in omni_dict.get("multiverses", []):
        # Multiverse-level archetypes and axioms
        mv_axioms = [Axiom(**ax) for ax in mv.get("axioms", [])]
        mv_archetypes = [ArchetypeEntity(**arc) for arc in mv.get("archetypes", [])]

        universes: list[Universe] = []
        for u in mv.get("universes", []):
            # Universe-level archetypes and axioms
            u_axioms = [Axiom(**ax) for ax in u.get("axioms", [])]
            u_archetypes = [ArchetypeEntity(**arc) for arc in u.get("archetypes", [])]

            # Arcs
            arcs = [Arc(**a, universe_id=u.get("id")) for a in u.get("arcs", [])]

            # Stories and Scenes
            stories: list[Story] = []
            for st in u.get("stories", []):
                scenes = [Scene(**sc, story_id=st.get("id")) for sc in st.get("scenes", [])]
                events = (
                    [
                        Event(**ev, story_id=st.get("id"), universe_id=u.get("id"))
                        for ev in st.get("events", [])
                    ]
                    if st.get("events")
                    else []
                )
                story = Story(
                    id=st.get("id"),
                    title=st.get("title"),
                    summary=st.get("summary"),
                    universe_id=u.get("id"),
                    arc_id=st.get("arc_id"),
                    system_id=st.get("system_id"),
                    scenes=scenes,
                    events=events,
                    sheets=[],
                )
                stories.append(story)

            # Entities and Sheets
            entities: list[ConcreteEntity] = []
            for e in u.get("entities", []):
                ce = ConcreteEntity(
                    id=e["id"],
                    name=e["name"],
                    universe_id=u.get("id"),
                    archetype_id=e.get("archetype_id"),
                    type=e.get("type", "manifestation"),
                    attributes=e.get("attributes", {}),
                    system_id=e.get("system_id"),
                )
                # Convert sheets and attach to entity
                for sh in e.get("sheets", []):
                    sheet = Sheet(
                        id=sh.get("id"),
                        name=sh.get("name"),
                        type=sh.get("type"),
                        attributes=sh.get("attributes", {}),
                        entity_id=ce.id,
                        story_id=sh.get("story_id"),
                        system_id=sh.get("system_id"),
                    )
                    ce.sheets.append(sheet)
                entities.append(ce)

            # Facts
            facts: list[Fact] = []
            for f in u.get("facts", []):
                participants = [FactParticipant(**p) for p in f.get("participants", [])]
                facts.append(
                    Fact(
                        id=f.get("id"),
                        universe_id=u.get("id"),
                        description=f.get("description"),
                        when=f.get("when"),
                        time_span=f.get("time_span"),
                        occurs_in=f.get("occurs_in"),
                        participants=participants,
                        source_refs=f.get("source_refs", []),
                        confidence=f.get("confidence"),
                        derived_from=f.get("derived_from", []),
                    )
                )

            # Relation states
            relation_states: list[RelationState] = []
            for rs in u.get("relation_states", []):
                relation_states.append(RelationState(**rs))

            uni = Universe(
                id=u.get("id"),
                name=u.get("name"),
                description=u.get("description"),
                stories=stories,
                arcs=arcs,
                entities=entities,
                system_id=u.get("system_id"),
                axioms=u_axioms,
                archetypes=u_archetypes,
                facts=facts,
                relation_states=relation_states,
            )
            universes.append(uni)

        m = Multiverse(
            id=mv.get("id"),
            name=mv.get("name"),
            description=mv.get("description"),
            universes=universes,
            axioms=mv_axioms,
            archetypes=mv_archetypes,
        )
        multiverses.append(m)

    omni = Omniverse(
        id=omni_dict["id"],
        name=omni_dict["name"],
        multiverses=multiverses,
    )
    return omni
