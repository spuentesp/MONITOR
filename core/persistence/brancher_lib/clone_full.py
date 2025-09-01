from __future__ import annotations

from typing import Any


class CloneFullMixin:
    def clone_universe_full(
        self,
        source_universe_id: str,
        new_universe_id: str,
        new_universe_name: str | None = None,
        *,
        force: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        # Guardrails
        self._check_source_and_target(source_universe_id, new_universe_id, force)
        if dry_run:
            stories = self._first_count(
                self.repo.run(
                    "MATCH (:Universe {id:$src})-[:HAS_STORY]->(st:Story) RETURN count(DISTINCT st) AS c",
                    src=source_universe_id,
                )
            )
            scenes = self._first_count(
                self.repo.run(
                    "MATCH (:Universe {id:$src})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(sc:Scene) RETURN count(DISTINCT sc) AS c",
                    src=source_universe_id,
                )
            )
            entities = self._first_count(
                self.repo.run(
                    "MATCH (:Universe {id:$src})<-[:BELONGS_TO]-(e:Entity) RETURN count(DISTINCT e) AS c",
                    src=source_universe_id,
                )
            )
            facts = self._first_count(
                self.repo.run(
                    "MATCH (:Universe {id:$src})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(sc:Scene) MATCH (f:Fact)-[:OCCURS_IN]->(sc) RETURN count(DISTINCT f) AS c",
                    src=source_universe_id,
                )
            )
            sheets = self._first_count(
                self.repo.run(
                    "MATCH (:Universe {id:$src})<-[:BELONGS_TO]-(:Entity)-[:HAS_SHEET]->(sh:Sheet) RETURN count(DISTINCT sh) AS c",
                    src=source_universe_id,
                )
            )
            rel_states = self._first_count(
                self.repo.run(
                    """
                MATCH (:Universe {id:$src})<-[:BELONGS_TO]-(eAll:Entity)
                WITH collect(eAll.id) AS eids
                MATCH (rs:RelationState)-[:REL_STATE_FOR {endpoint:'A'}]->(a:Entity)
                MATCH (rs)-[:REL_STATE_FOR {endpoint:'B'}]->(b:Entity)
                WHERE a.id IN eids AND b.id IN eids
                RETURN count(DISTINCT rs) AS c
                """,
                    src=source_universe_id,
                )
            )
            arcs = self._first_count(
                self.repo.run(
                    "MATCH (:Universe {id:$src})-[:HAS_ARC]->(a:Arc) RETURN count(DISTINCT a) AS c",
                    src=source_universe_id,
                )
            )
            return {
                "dry_run": True,
                "new_universe_id": new_universe_id,
                "branched_from_universe": source_universe_id,
                "counts": {
                    "stories": stories,
                    "scenes": scenes,
                    "entities": entities,
                    "facts": facts,
                    "sheets": sheets,
                    "relation_states": rel_states,
                    "arcs": arcs,
                },
            }
        """
        Deep clone an entire Universe, including:
        - Stories and Scenes (with sequence_index), and their USES_SYSTEM relations.
        - Entities (BELONGS_TO), APPEARS_IN edges to cloned scenes, USES_SYSTEM.
        - Facts (OCCURS_IN cloned scenes), PARTICIPATES_AS to cloned entities.
        - Sheets (HAS_SHEET rel copy with props), USES_SYSTEM.
        - RelationState entries rewired to cloned entities and cloned provenance scenes.
        - Arcs and Arc->Story ordering, attached to the new Universe.
        - Axiom APPLIES_TO and Universe/Story/Entity/Sheet USES_SYSTEM carried over.
        Provenance: BRANCHED_FROM edges from every cloned node to original counterparts.
        IDs are namespaced as f"{new_universe_id}/{original_id}" for cloned nodes, and
        f"{new_universe_id}/{story_id}/{scene_id}" for scenes.
        """
        # Create new Universe, attach to same Multiverse, copy USES_SYSTEM and Axiom APPLIES_TO
        self.repo.run(
            """
            MATCH (u:Universe {id:$src_uid})
            OPTIONAL MATCH (m:Multiverse)-[:HAS_UNIVERSE]->(u)
            MERGE (u2:Universe {id:$new_uid})
            SET u2.name = coalesce($name, u.name + ' [clone]'),
                u2.description = coalesce(u.description,'') + ' (cloned)'
            WITH u, u2, m
            FOREACH (_ IN CASE WHEN m IS NULL THEN [] ELSE [1] END | MERGE (m)-[:HAS_UNIVERSE]->(u2))
            MERGE (u2)-[:BRANCHED_FROM]->(u)
            WITH u, u2
            OPTIONAL MATCH (u)-[:USES_SYSTEM]->(sys:System)
            FOREACH (_ IN CASE WHEN sys IS NULL THEN [] ELSE [1] END | MERGE (u2)-[:USES_SYSTEM]->(sys))
            WITH u, u2
            OPTIONAL MATCH (a:Axiom)-[:APPLIES_TO]->(u)
            FOREACH (_ IN CASE WHEN a IS NULL THEN [] ELSE [1] END | MERGE (a)-[:APPLIES_TO]->(u2))
            """,
            src_uid=source_universe_id,
            new_uid=new_universe_id,
            name=new_universe_name,
        )

        # Clone Stories and USES_SYSTEM, attach to u2
        self.repo.run(
            """
            MATCH (u:Universe {id:$src_uid})-[:HAS_STORY]->(st:Story)
            WITH st
            MERGE (st2:Story {id: $new_uid + '/' + st.id})
            SET st2 += st
            WITH st, st2
            MATCH (u2:Universe {id:$new_uid})
            MERGE (u2)-[:HAS_STORY]->(st2)
            MERGE (st2)-[:BRANCHED_FROM]->(st)
            WITH st, st2
            OPTIONAL MATCH (st)-[:USES_SYSTEM]->(sys:System)
            FOREACH (_ IN CASE WHEN sys IS NULL THEN [] ELSE [1] END | MERGE (st2)-[:USES_SYSTEM]->(sys))
            """,
            src_uid=source_universe_id,
            new_uid=new_universe_id,
        )

        # Clone Scenes per story
        self.repo.run(
            """
            MATCH (u:Universe {id:$src_uid})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
            WITH st, sc
            MERGE (sc2:Scene {id: $new_uid + '/' + st.id + '/' + sc.id})
            SET sc2 += sc
            WITH st, sc, sc2
            MATCH (st2:Story {id: $new_uid + '/' + st.id})
            MERGE (st2)-[:HAS_SCENE {sequence_index: sc.sequence_index}]->(sc2)
            MERGE (sc2)-[:BRANCHED_FROM]->(sc)
            """,
            src_uid=source_universe_id,
            new_uid=new_universe_id,
        )

        # Clone Entities of the universe and APPEARS_IN to cloned scenes, carry USES_SYSTEM
        self.repo.run(
            """
            MATCH (u:Universe {id:$src_uid})<-[:BELONGS_TO]-(e:Entity)
            MERGE (e2:Entity {id: $new_uid + '/' + e.id})
            SET e2 += e
            WITH e, e2
            MATCH (u2:Universe {id:$new_uid})
            MERGE (e2)-[:BELONGS_TO]->(u2)
            MERGE (e2)-[:BRANCHED_FROM]->(e)
            WITH e, e2
            OPTIONAL MATCH (e)-[:USES_SYSTEM]->(sys:System)
            FOREACH (_ IN CASE WHEN sys IS NULL THEN [] ELSE [1] END | MERGE (e2)-[:USES_SYSTEM]->(sys))
            """,
            src_uid=source_universe_id,
            new_uid=new_universe_id,
        )
        # APPEARS_IN to cloned scenes
        self.repo.run(
            """
            MATCH (u:Universe {id:$src_uid})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
            MATCH (e:Entity)-[:APPEARS_IN]->(sc)
            WITH st, sc, e
            MATCH (e2:Entity {id: $new_uid + '/' + e.id})
            MATCH (sc2:Scene {id: $new_uid + '/' + st.id + '/' + sc.id})
            MERGE (e2)-[:APPEARS_IN]->(sc2)
            """,
            src_uid=source_universe_id,
            new_uid=new_universe_id,
        )

        # Clone Facts and PARTICIPATES_AS
        self.repo.run(
            """
            MATCH (u:Universe {id:$src_uid})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
            MATCH (f:Fact)-[:OCCURS_IN]->(sc)
            WITH DISTINCT st, sc, f
            MERGE (f2:Fact {id: $new_uid + '/' + f.id})
            SET f2 += f
            WITH st, sc, f, f2
            MATCH (sc2:Scene {id: $new_uid + '/' + st.id + '/' + sc.id})
            MERGE (f2)-[:OCCURS_IN]->(sc2)
            MERGE (f2)-[:BRANCHED_FROM]->(f)
            """,
            src_uid=source_universe_id,
            new_uid=new_universe_id,
        )
        self.repo.run(
            """
            MATCH (u:Universe {id:$src_uid})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(sc:Scene)
            MATCH (f:Fact)-[:OCCURS_IN]->(sc)
            MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
            WITH DISTINCT e, f, p
            MATCH (e2:Entity {id: $new_uid + '/' + e.id})
            MATCH (f2:Fact {id: $new_uid + '/' + f.id})
            MERGE (e2)-[:PARTICIPATES_AS {role: p.role}]->(f2)
            """,
            src_uid=source_universe_id,
            new_uid=new_universe_id,
        )

        # Clone Sheets and their USES_SYSTEM; copy HAS_SHEET properties
        self.repo.run(
            """
            MATCH (u:Universe {id:$src_uid})<-[:BELONGS_TO]-(e:Entity)-[hs:HAS_SHEET]->(sh:Sheet)
            WITH e, hs, sh
            MATCH (e2:Entity {id: $new_uid + '/' + e.id})
            MERGE (sh2:Sheet {id: $new_uid + '/' + sh.id})
            SET sh2 += sh
            MERGE (e2)-[hs2:HAS_SHEET]->(sh2)
            SET hs2.story_id = hs.story_id, hs2.system_id = hs.system_id
            MERGE (sh2)-[:BRANCHED_FROM]->(sh)
            WITH sh, sh2
            OPTIONAL MATCH (sh)-[:USES_SYSTEM]->(sys:System)
            FOREACH (_ IN CASE WHEN sys IS NULL THEN [] ELSE [1] END | MERGE (sh2)-[:USES_SYSTEM]->(sys))
            """,
            src_uid=source_universe_id,
            new_uid=new_universe_id,
        )

        # Clone RelationState, rewiring endpoints to cloned entities and provenance scenes to cloned scenes
        self.repo.run(
            """
            MATCH (u:Universe {id:$src_uid})<-[:BELONGS_TO]-(eAll:Entity)
            WITH collect(eAll.id) AS eids
            MATCH (rs:RelationState)
            MATCH (rs)-[:REL_STATE_FOR {endpoint:'A'}]->(a:Entity)
            MATCH (rs)-[:REL_STATE_FOR {endpoint:'B'}]->(b:Entity)
            WHERE a.id IN eids AND b.id IN eids
            OPTIONAL MATCH (s1:Scene)<-[:SET_IN_SCENE]-(rs)
            OPTIONAL MATCH (s2:Scene)<-[:CHANGED_IN_SCENE]-(rs)
            OPTIONAL MATCH (s3:Scene)<-[:ENDED_IN_SCENE]-(rs)
            MERGE (rs2:RelationState {id: $new_uid + '/' + rs.id})
            SET rs2 += rs
            WITH rs, rs2, a, b, s1, s2, s3
            MATCH (a2:Entity {id: $new_uid + '/' + a.id})
            MATCH (b2:Entity {id: $new_uid + '/' + b.id})
            MERGE (rs2)-[:REL_STATE_FOR {endpoint:'A'}]->(a2)
            MERGE (rs2)-[:REL_STATE_FOR {endpoint:'B'}]->(b2)
            MERGE (rs2)-[:BRANCHED_FROM]->(rs)
            WITH rs2, s1, s2, s3
            OPTIONAL MATCH (st1:Story)-[:HAS_SCENE]->(s1)
            OPTIONAL MATCH (st2:Story)-[:HAS_SCENE]->(s2)
            OPTIONAL MATCH (st3:Story)-[:HAS_SCENE]->(s3)
            OPTIONAL MATCH (s1c:Scene {id: $new_uid + '/' + st1.id + '/' + s1.id})
            FOREACH (_ IN CASE WHEN s1c IS NULL THEN [] ELSE [1] END | MERGE (rs2)-[:SET_IN_SCENE]->(s1c))
            OPTIONAL MATCH (s2c:Scene {id: $new_uid + '/' + st2.id + '/' + s2.id})
            FOREACH (_ IN CASE WHEN s2c IS NULL THEN [] ELSE [1] END | MERGE (rs2)-[:CHANGED_IN_SCENE]->(s2c))
            OPTIONAL MATCH (s3c:Scene {id: $new_uid + '/' + st3.id + '/' + s3.id})
            FOREACH (_ IN CASE WHEN s3c IS NULL THEN [] ELSE [1] END | MERGE (rs2)-[:ENDED_IN_SCENE]->(s3c))
            """,
            src_uid=source_universe_id,
            new_uid=new_universe_id,
        )

        # Clone Arcs and relate to cloned stories with preserved ordering
        self.repo.run(
            """
            MATCH (u:Universe {id:$src_uid})-[:HAS_ARC]->(a:Arc)
            MERGE (a2:Arc {id: $new_uid + '/' + a.id})
            SET a2 += a
            WITH a, a2
            MATCH (u2:Universe {id:$new_uid})
            MERGE (u2)-[:HAS_ARC]->(a2)
            MERGE (a2)-[:BRANCHED_FROM]->(a)
            """,
            src_uid=source_universe_id,
            new_uid=new_universe_id,
        )
        self.repo.run(
            """
            MATCH (u:Universe {id:$src_uid})-[:HAS_ARC]->(a:Arc)-[r:HAS_STORY]->(st:Story)
            MATCH (a2:Arc {id: $new_uid + '/' + a.id})
            MATCH (st2:Story {id: $new_uid + '/' + st.id})
            MERGE (a2)-[:HAS_STORY {sequence_index: r.sequence_index}]->(st2)
            """,
            src_uid=source_universe_id,
            new_uid=new_universe_id,
        )

        return {"new_universe_id": new_universe_id, "branched_from_universe": source_universe_id}
