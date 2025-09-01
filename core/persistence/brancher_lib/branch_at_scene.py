from __future__ import annotations

from typing import Any


class BranchAtSceneMixin:
    def branch_universe_at_scene(
        self,
        source_universe_id: str,
        divergence_scene_id: str,
        new_universe_id: str,
        new_universe_name: str | None = None,
        *,
        force: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
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
