from __future__ import annotations

from typing import Any, Dict

from core.persistence.neo4j_repo import Neo4jRepo


class BranchService:
    """
    What-if branching: clone a universe subgraph up to a divergence scene.

    Contract (initial version):
    - Inputs: source_universe_id, divergence_scene_id, new_universe_id, optional new_universe_name
    - Behavior:
      * Create a new Universe and BRANCHED_FROM -> old Universe (provenance with story/scene/seq).
      * Attach new Universe to the same Multiverse and copy USES_SYSTEM and APPLIES_TO (axioms) edges.
      * Clone the Story that contains the divergence scene into a new Story under the new Universe.
      * Clone Scenes up to and including the divergence scene (by sequence_index) and link to new Story.
      * Clone Entities that appear in included scenes; attach to new Universe; copy USES_SYSTEM.
      * Clone Facts that occur in included scenes; copy OCCURS_IN; clone PARTICIPATES_AS to cloned entities.
      * Clone Sheets for cloned entities where HAS_SHEET.story_id == original story; copy USES_SYSTEM.
      * Clone RelationState records whose provenance scenes are included; rewire to cloned entities and scenes.
      * Add BRANCHED_FROM edges from each cloned node to its original counterpart.
    - IDs: new ids are namespaced as f"{new_universe_id}/{original_id}" for cloned nodes.
    - Output: summary dict with new ids.
    """

    def __init__(self, repo: Neo4jRepo):
        self.repo = repo

    def _check_source_and_target(self, source_universe_id: str, new_universe_id: str, force: bool) -> None:
        rows = self.repo.run(
            """
            OPTIONAL MATCH (src:Universe {id:$src})
            OPTIONAL MATCH (tgt:Universe {id:$tgt})
            RETURN src IS NOT NULL AS src_ok, tgt IS NOT NULL AS tgt_exists
            """,
            src=source_universe_id,
            tgt=new_universe_id,
        )
        src_ok = rows and rows[0].get("src_ok", False)
        tgt_exists = rows and rows[0].get("tgt_exists", False)
        if not src_ok:
            raise ValueError("Source universe not found")
        if tgt_exists and not force:
            raise ValueError("Target universe already exists; use --force to overwrite or choose a new id")

    @staticmethod
    def _first_count(rows) -> int:
        return int(rows[0]["c"]) if rows and "c" in rows[0] else 0

    def branch_universe_at_scene(
        self,
        source_universe_id: str,
        divergence_scene_id: str,
        new_universe_id: str,
        new_universe_name: str | None = None,
        *,
        force: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        # Guardrails
        self._check_source_and_target(source_universe_id, new_universe_id, force)
        # 1) Resolve story and sequence index for divergence
        rows = self.repo.run(
            """
            MATCH (u:Universe {id:$src_uid})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene {id:$sid})
            RETURN st.id AS story_id, sc.sequence_index AS idx
            LIMIT 1
            """,
            src_uid=source_universe_id,
            sid=divergence_scene_id,
        )
        if not rows:
            raise ValueError("Divergence scene not found under source universe")
        story_id = rows[0]["story_id"]
        seq_idx = rows[0]["idx"]
        new_story_id = f"{new_universe_id}/{story_id}"

        if dry_run:
            # Compute counts only; do not write
            scenes = self._first_count(
                self.repo.run(
                    """
                    MATCH (:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
                    WHERE sc.sequence_index <= $idx
                    RETURN count(DISTINCT sc) AS c
                    """,
                    sid=story_id,
                    idx=seq_idx,
                )
            )
            entities = self._first_count(
                self.repo.run(
                    """
                    MATCH (:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
                    WHERE sc.sequence_index <= $idx
                    MATCH (e:Entity)-[:APPEARS_IN]->(sc)
                    RETURN count(DISTINCT e) AS c
                    """,
                    sid=story_id,
                    idx=seq_idx,
                )
            )
            facts = self._first_count(
                self.repo.run(
                    """
                    MATCH (:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
                    WHERE sc.sequence_index <= $idx
                    MATCH (f:Fact)-[:OCCURS_IN]->(sc)
                    RETURN count(DISTINCT f) AS c
                    """,
                    sid=story_id,
                    idx=seq_idx,
                )
            )
            sheets = self._first_count(
                self.repo.run(
                    """
                    MATCH (:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
                    WHERE sc.sequence_index <= $idx
                    MATCH (e:Entity)-[:APPEARS_IN]->(sc)
                    MATCH (e)-[hs:HAS_SHEET]->(:Sheet)
                    WHERE hs.story_id = $sid
                    RETURN count(DISTINCT hs) AS c
                    """,
                    sid=story_id,
                    idx=seq_idx,
                )
            )
            rel_states = self._first_count(
                self.repo.run(
                    """
                    MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
                    WHERE sc.sequence_index <= $idx
                    WITH collect(sc.id) AS included
                    MATCH (rs:RelationState)
                    OPTIONAL MATCH (rs)-[:SET_IN_SCENE]->(s1:Scene)
                    OPTIONAL MATCH (rs)-[:CHANGED_IN_SCENE]->(s2:Scene)
                    OPTIONAL MATCH (rs)-[:ENDED_IN_SCENE]->(s3:Scene)
                    WITH rs, s1, s2, s3, included
                    WHERE (s1.id IN included) OR (s2.id IN included) OR (s3.id IN included)
                    RETURN count(DISTINCT rs) AS c
                    """,
                    sid=story_id,
                    idx=seq_idx,
                )
            )
            return {
                "dry_run": True,
                "new_universe_id": new_universe_id,
                "new_story_id": new_story_id,
                "branched_from_universe": source_universe_id,
                "divergence_scene_id": divergence_scene_id,
                "divergence_story_id": story_id,
                "divergence_sequence_index": seq_idx,
                "counts": {
                    "stories": 1,
                    "scenes": scenes,
                    "entities": entities,
                    "facts": facts,
                    "sheets": sheets,
                    "relation_states": rel_states,
                },
            }

        # 2) Create new Universe with provenance and shared attachments
        self.repo.run(
            """
            MATCH (u:Universe {id:$src_uid})
            OPTIONAL MATCH (m:Multiverse)-[:HAS_UNIVERSE]->(u)
            MERGE (u2:Universe {id:$new_uid})
            SET u2.name = coalesce($name, u.name + ' [branch]'),
                u2.description = coalesce(u.description,'') + ' (branched at ' + $sid + ')'
            WITH u, u2, m
            FOREACH (_ IN CASE WHEN m IS NULL THEN [] ELSE [1] END | MERGE (m)-[:HAS_UNIVERSE]->(u2))
            MERGE (u2)-[:BRANCHED_FROM {at_scene:$sid, story_id:$story_id, sequence_index:$idx}]->(u)
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
            sid=divergence_scene_id,
            story_id=story_id,
            idx=seq_idx,
        )

        # 3) Clone Story and its system usage
        self.repo.run(
            """
            MATCH (st:Story {id:$sid})
            MERGE (st2:Story {id:$new_sid})
            SET st2 += st
            WITH st, st2
            MATCH (u2:Universe {id:$new_uid})
            MERGE (u2)-[:HAS_STORY]->(st2)
            MERGE (st2)-[:BRANCHED_FROM]->(st)
            WITH st, st2
            OPTIONAL MATCH (st)-[:USES_SYSTEM]->(sys:System)
            FOREACH (_ IN CASE WHEN sys IS NULL THEN [] ELSE [1] END | MERGE (st2)-[:USES_SYSTEM]->(sys))
            """,
            sid=story_id,
            new_sid=new_story_id,
            new_uid=new_universe_id,
        )

        # 4) Clone Scenes up to divergence
        self.repo.run(
            """
            MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
            WHERE sc.sequence_index <= $idx
            WITH sc ORDER BY sc.sequence_index
            MERGE (sc2:Scene {id: $new_sid + '/' + sc.id})
            SET sc2 += sc
            WITH sc, sc2
            MATCH (st2:Story {id:$new_sid})
            MERGE (st2)-[:HAS_SCENE {sequence_index: sc.sequence_index}]->(sc2)
            MERGE (sc2)-[:BRANCHED_FROM]->(sc)
            """,
            sid=story_id,
            new_sid=new_story_id,
            idx=seq_idx,
        )

        # 5) Clone Entities that appear in included scenes, attach to new universe and APPEARS_IN new scenes
        self.repo.run(
            """
            MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
            WHERE sc.sequence_index <= $idx
            MATCH (e:Entity)-[:APPEARS_IN]->(sc)
            WITH DISTINCT e
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
            sid=story_id,
            idx=seq_idx,
            new_uid=new_universe_id,
        )
        # APPEARS_IN edges to cloned scenes
        self.repo.run(
            """
            MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
            WHERE sc.sequence_index <= $idx
            MATCH (e:Entity)-[:APPEARS_IN]->(sc)
            WITH e, sc
            MATCH (e2:Entity {id: $new_uid + '/' + e.id})
            MATCH (sc2:Scene {id: $new_sid + '/' + sc.id})
            MERGE (e2)-[:APPEARS_IN]->(sc2)
            """,
            sid=story_id,
            idx=seq_idx,
            new_uid=new_universe_id,
            new_sid=new_story_id,
        )

        # 6) Clone Facts for included scenes and PARTICIPATES_AS links
        self.repo.run(
            """
            MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
            WHERE sc.sequence_index <= $idx
            MATCH (f:Fact)-[:OCCURS_IN]->(sc)
            WITH DISTINCT f, sc
            MERGE (f2:Fact {id: $new_uid + '/' + f.id})
            SET f2 += f
            WITH f, f2, sc
            MATCH (sc2:Scene {id: $new_sid + '/' + sc.id})
            MERGE (f2)-[:OCCURS_IN]->(sc2)
            MERGE (f2)-[:BRANCHED_FROM]->(f)
            """,
            sid=story_id,
            idx=seq_idx,
            new_uid=new_universe_id,
            new_sid=new_story_id,
        )
        self.repo.run(
            """
            MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(sc:Scene)
            WHERE sc.sequence_index <= $idx
            MATCH (f:Fact)-[:OCCURS_IN]->(sc)
            MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
            WITH DISTINCT e, f, p
            MATCH (e2:Entity {id: $new_uid + '/' + e.id})
            MATCH (f2:Fact {id: $new_uid + '/' + f.id})
            MERGE (e2)-[:PARTICIPATES_AS {role: p.role}]->(f2)
            """,
            sid=story_id,
            idx=seq_idx,
            new_uid=new_universe_id,
        )

        # 7) Clone Sheets for cloned entities tied to original story via HAS_SHEET.story_id
        self.repo.run(
            """
            MATCH (e:Entity)-[hs:HAS_SHEET]->(sh:Sheet)
            WHERE hs.story_id = $sid
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
            sid=story_id,
            new_uid=new_universe_id,
        )

        # 8) Clone RelationState entries whose provenance scenes are included
        self.repo.run(
            """
            MATCH (st:Story {id:$sid})-[:HAS_SCENE]->(scInc:Scene)
            WHERE scInc.sequence_index <= $idx
            WITH collect(scInc.id) AS included
            MATCH (rs:RelationState)
            OPTIONAL MATCH (rs)-[:SET_IN_SCENE]->(s1:Scene)
            OPTIONAL MATCH (rs)-[:CHANGED_IN_SCENE]->(s2:Scene)
            OPTIONAL MATCH (rs)-[:ENDED_IN_SCENE]->(s3:Scene)
            WITH rs, s1, s2, s3, included
            WHERE (s1.id IN included) OR (s2.id IN included) OR (s3.id IN included)
            MERGE (rs2:RelationState {id: $new_uid + '/' + rs.id})
            SET rs2 += rs
            WITH rs, rs2
            MATCH (rs)-[:REL_STATE_FOR {endpoint:'A'}]->(a:Entity)
            MATCH (rs)-[:REL_STATE_FOR {endpoint:'B'}]->(b:Entity)
            MATCH (a2:Entity {id: $new_uid + '/' + a.id})
            MATCH (b2:Entity {id: $new_uid + '/' + b.id})
            MERGE (rs2)-[:REL_STATE_FOR {endpoint:'A'}]->(a2)
            MERGE (rs2)-[:REL_STATE_FOR {endpoint:'B'}]->(b2)
            MERGE (rs2)-[:BRANCHED_FROM]->(rs)
            WITH rs, rs2, s1, s2, s3
            OPTIONAL MATCH (s1c:Scene {id: $new_sid + '/' + s1.id})
            FOREACH (_ IN CASE WHEN s1c IS NULL THEN [] ELSE [1] END | MERGE (rs2)-[:SET_IN_SCENE]->(s1c))
            OPTIONAL MATCH (s2c:Scene {id: $new_sid + '/' + s2.id})
            FOREACH (_ IN CASE WHEN s2c IS NULL THEN [] ELSE [1] END | MERGE (rs2)-[:CHANGED_IN_SCENE]->(s2c))
            OPTIONAL MATCH (s3c:Scene {id: $new_sid + '/' + s3.id})
            FOREACH (_ IN CASE WHEN s3c IS NULL THEN [] ELSE [1] END | MERGE (rs2)-[:ENDED_IN_SCENE]->(s3c))
            """,
            sid=story_id,
            idx=seq_idx,
            new_uid=new_universe_id,
            new_sid=new_story_id,
        )

        return {
            "new_universe_id": new_universe_id,
            "new_story_id": new_story_id,
            "branched_from_universe": source_universe_id,
            "divergence_scene_id": divergence_scene_id,
            "divergence_story_id": story_id,
            "divergence_sequence_index": seq_idx,
        }

    def clone_universe_full(
        self,
        source_universe_id: str,
        new_universe_id: str,
        new_universe_name: str | None = None,
        *,
        force: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        # Guardrails
        self._check_source_and_target(source_universe_id, new_universe_id, force)
        if dry_run:
            stories = self._first_count(self.repo.run(
                "MATCH (:Universe {id:$src})-[:HAS_STORY]->(st:Story) RETURN count(DISTINCT st) AS c",
                src=source_universe_id,
            ))
            scenes = self._first_count(self.repo.run(
                "MATCH (:Universe {id:$src})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(sc:Scene) RETURN count(DISTINCT sc) AS c",
                src=source_universe_id,
            ))
            entities = self._first_count(self.repo.run(
                "MATCH (:Universe {id:$src})<-[:BELONGS_TO]-(e:Entity) RETURN count(DISTINCT e) AS c",
                src=source_universe_id,
            ))
            facts = self._first_count(self.repo.run(
                "MATCH (:Universe {id:$src})-[:HAS_STORY]->(:Story)-[:HAS_SCENE]->(sc:Scene) MATCH (f:Fact)-[:OCCURS_IN]->(sc) RETURN count(DISTINCT f) AS c",
                src=source_universe_id,
            ))
            sheets = self._first_count(self.repo.run(
                "MATCH (:Universe {id:$src})<-[:BELONGS_TO]-(:Entity)-[:HAS_SHEET]->(sh:Sheet) RETURN count(DISTINCT sh) AS c",
                src=source_universe_id,
            ))
            rel_states = self._first_count(self.repo.run(
                """
                MATCH (:Universe {id:$src})<-[:BELONGS_TO]-(eAll:Entity)
                WITH collect(eAll.id) AS eids
                MATCH (rs:RelationState)-[:REL_STATE_FOR {endpoint:'A'}]->(a:Entity)
                MATCH (rs)-[:REL_STATE_FOR {endpoint:'B'}]->(b:Entity)
                WHERE a.id IN eids AND b.id IN eids
                RETURN count(DISTINCT rs) AS c
                """,
                src=source_universe_id,
            ))
            arcs = self._first_count(self.repo.run(
                "MATCH (:Universe {id:$src})-[:HAS_ARC]->(a:Arc) RETURN count(DISTINCT a) AS c",
                src=source_universe_id,
            ))
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

    def clone_universe_subset(
        self,
        source_universe_id: str,
        new_universe_id: str,
        new_universe_name: str | None = None,
        stories: list[str] | None = None,
        arcs: list[str] | None = None,
        scene_max_index: int | None = None,
        include_all_entities: bool = False,
        *,
        force: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        # Guardrails
        self._check_source_and_target(source_universe_id, new_universe_id, force)
        stories = stories or []
        arcs = arcs or []
        if dry_run:
            stories_cnt = self._first_count(self.repo.run(
                "MATCH (:Universe {id:$src})-[:HAS_STORY]->(st:Story) WHERE size($stories)=0 OR st.id IN $stories RETURN count(DISTINCT st) AS c",
                src=source_universe_id,
                stories=stories,
            ))
            scenes_cnt = self._first_count(self.repo.run(
                """
                MATCH (:Universe {id:$src})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
                WHERE (size($stories)=0 OR st.id IN $stories) AND ($scene_max IS NULL OR sc.sequence_index <= $scene_max)
                RETURN count(DISTINCT sc) AS c
                """,
                src=source_universe_id,
                stories=stories,
                scene_max=scene_max_index,
            ))
            if include_all_entities:
                entities_cnt = self._first_count(self.repo.run(
                    "MATCH (:Universe {id:$src})<-[:BELONGS_TO]-(e:Entity) RETURN count(DISTINCT e) AS c",
                    src=source_universe_id,
                ))
            else:
                entities_cnt = self._first_count(self.repo.run(
                    """
                    MATCH (:Universe {id:$src})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
                    WHERE (size($stories)=0 OR st.id IN $stories) AND ($scene_max IS NULL OR sc.sequence_index <= $scene_max)
                    MATCH (e:Entity)-[:APPEARS_IN]->(sc)
                    RETURN count(DISTINCT e) AS c
                    """,
                    src=source_universe_id,
                    stories=stories,
                    scene_max=scene_max_index,
                ))
            facts_cnt = self._first_count(self.repo.run(
                """
                MATCH (:Universe {id:$src})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
                WHERE (size($stories)=0 OR st.id IN $stories) AND ($scene_max IS NULL OR sc.sequence_index <= $scene_max)
                MATCH (f:Fact)-[:OCCURS_IN]->(sc)
                RETURN count(DISTINCT f) AS c
                """,
                src=source_universe_id,
                stories=stories,
                scene_max=scene_max_index,
            ))
            sheets_cnt = self._first_count(self.repo.run(
                "MATCH (:Universe {id:$src})<-[:BELONGS_TO]-(:Entity)-[:HAS_SHEET]->(sh:Sheet) RETURN count(DISTINCT sh) AS c",
                src=source_universe_id,
            ))
            arcs_cnt = self._first_count(self.repo.run(
                "MATCH (:Universe {id:$src})-[:HAS_ARC]->(a:Arc) WHERE size($arcs)=0 OR a.id IN $arcs RETURN count(DISTINCT a) AS c",
                src=source_universe_id,
                arcs=arcs,
            ))
            return {
                "dry_run": True,
                "new_universe_id": new_universe_id,
                "branched_from_universe": source_universe_id,
                "counts": {
                    "stories": stories_cnt,
                    "scenes": scenes_cnt,
                    "entities": entities_cnt,
                    "facts": facts_cnt,
                    "sheets": sheets_cnt,
                    "arcs": arcs_cnt,
                },
            }
        # 1) New universe, attach, copy USES_SYSTEM and axioms
        self.repo.run(
            """
            MATCH (u:Universe {id:$src_uid})
            OPTIONAL MATCH (m:Multiverse)-[:HAS_UNIVERSE]->(u)
            MERGE (u2:Universe {id:$new_uid})
            SET u2.name = coalesce($name, u.name + ' [subset]'),
                u2.description = coalesce(u.description,'') + ' (subset clone)'
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
        # 2) Stories (filtered) and their USES_SYSTEM
        self.repo.run(
            """
            WITH $stories AS stories
            MATCH (u:Universe {id:$src_uid})-[:HAS_STORY]->(st:Story)
            WHERE size(stories)=0 OR st.id IN stories
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
            stories=stories,
        )
        # 3) Scenes (filtered by story and optional max index)
        self.repo.run(
            """
            WITH $stories AS stories, $scene_max AS scene_max
            MATCH (u:Universe {id:$src_uid})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
            WHERE (size(stories)=0 OR st.id IN stories) AND (scene_max IS NULL OR sc.sequence_index <= scene_max)
            MERGE (sc2:Scene {id: $new_uid + '/' + st.id + '/' + sc.id})
            SET sc2 += sc
            WITH st, sc, sc2
            MATCH (st2:Story {id: $new_uid + '/' + st.id})
            MERGE (st2)-[:HAS_SCENE {sequence_index: sc.sequence_index}]->(sc2)
            MERGE (sc2)-[:BRANCHED_FROM]->(sc)
            """,
            src_uid=source_universe_id,
            new_uid=new_universe_id,
            stories=stories,
            scene_max=scene_max_index,
        )
        # 4) Entities: all or only those in included scenes
        if include_all_entities:
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
        else:
            self.repo.run(
                """
                WITH $stories AS stories, $scene_max AS scene_max
                MATCH (u:Universe {id:$src_uid})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
                WHERE (size(stories)=0 OR st.id IN stories) AND (scene_max IS NULL OR sc.sequence_index <= scene_max)
                MATCH (e:Entity)-[:APPEARS_IN]->(sc)
                WITH DISTINCT e
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
                stories=stories,
                scene_max=scene_max_index,
            )
        # APPEARS_IN edges for included scenes
        self.repo.run(
            """
            WITH $stories AS stories, $scene_max AS scene_max
            MATCH (u:Universe {id:$src_uid})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
            WHERE (size(stories)=0 OR st.id IN stories) AND (scene_max IS NULL OR sc.sequence_index <= scene_max)
            MATCH (e:Entity)-[:APPEARS_IN]->(sc)
            WITH st, sc, e
            MATCH (e2:Entity {id: $new_uid + '/' + e.id})
            MATCH (sc2:Scene {id: $new_uid + '/' + st.id + '/' + sc.id})
            MERGE (e2)-[:APPEARS_IN]->(sc2)
            """,
            src_uid=source_universe_id,
            new_uid=new_universe_id,
            stories=stories,
            scene_max=scene_max_index,
        )
        # 5) Facts (from included scenes) and PARTICIPATES_AS
        self.repo.run(
            """
            WITH $stories AS stories, $scene_max AS scene_max
            MATCH (u:Universe {id:$src_uid})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
            WHERE (size(stories)=0 OR st.id IN stories) AND (scene_max IS NULL OR sc.sequence_index <= scene_max)
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
            stories=stories,
            scene_max=scene_max_index,
        )
        self.repo.run(
            """
            WITH $stories AS stories, $scene_max AS scene_max
            MATCH (u:Universe {id:$src_uid})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
            WHERE (size(stories)=0 OR st.id IN stories) AND (scene_max IS NULL OR sc.sequence_index <= scene_max)
            MATCH (f:Fact)-[:OCCURS_IN]->(sc)
            MATCH (e:Entity)-[p:PARTICIPATES_AS]->(f)
            WITH DISTINCT e, f, p
            MATCH (e2:Entity {id: $new_uid + '/' + e.id})
            MATCH (f2:Fact {id: $new_uid + '/' + f.id})
            MERGE (e2)-[:PARTICIPATES_AS {role: p.role}]->(f2)
            """,
            src_uid=source_universe_id,
            new_uid=new_universe_id,
            stories=stories,
            scene_max=scene_max_index,
        )
        # 6) Sheets for cloned entities (copy all sheets)
        self.repo.run(
            """
            MATCH (e2:Entity {id: $new_uid + '/' + e.id})
            WITH e2 LIMIT 0
            """,
            new_uid=new_universe_id,
        )
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
        # 7) RelationState for cloned entities
        self.repo.run(
            """
            MATCH (e2:Entity) WHERE e2.id STARTS WITH $new_uid + '/'
            WITH collect(replace(e2.id, $new_uid + '/', '')) AS original_eids
            MATCH (rs:RelationState)
            MATCH (rs)-[:REL_STATE_FOR {endpoint:'A'}]->(a:Entity)
            MATCH (rs)-[:REL_STATE_FOR {endpoint:'B'}]->(b:Entity)
            WHERE a.id IN original_eids AND b.id IN original_eids
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
            new_uid=new_universe_id,
        )
        # 8) Arcs (filtered) and ordering
        self.repo.run(
            """
            WITH $arcs AS arcs
            MATCH (u:Universe {id:$src_uid})-[:HAS_ARC]->(a:Arc)
            WHERE size(arcs)=0 OR a.id IN arcs
            MERGE (a2:Arc {id: $new_uid + '/' + a.id})
            SET a2 += a
            WITH a, a2
            MATCH (u2:Universe {id:$new_uid})
            MERGE (u2)-[:HAS_ARC]->(a2)
            MERGE (a2)-[:BRANCHED_FROM]->(a)
            """,
            src_uid=source_universe_id,
            new_uid=new_universe_id,
            arcs=arcs,
        )
        self.repo.run(
            """
            WITH $stories AS stories, $arcs AS arcs
            MATCH (u:Universe {id:$src_uid})-[:HAS_ARC]->(a:Arc)-[r:HAS_STORY]->(st:Story)
            WHERE (size(arcs)=0 OR a.id IN arcs) AND (size(stories)=0 OR st.id IN stories)
            MATCH (a2:Arc {id: $new_uid + '/' + a.id})
            MATCH (st2:Story {id: $new_uid + '/' + st.id})
            MERGE (a2)-[:HAS_STORY {sequence_index: r.sequence_index}]->(st2)
            """,
            src_uid=source_universe_id,
            new_uid=new_universe_id,
            stories=stories,
            arcs=arcs,
        )
        return {"new_universe_id": new_universe_id, "branched_from_universe": source_universe_id}
