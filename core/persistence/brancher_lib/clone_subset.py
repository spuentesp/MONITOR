from __future__ import annotations

from typing import Any


class CloneSubsetMixin:
    """
    Mixin for subset cloning operations.
    
    This mixin expects to be used with a base class that provides:
    - repo: repository object with run() method
    - _check_source_and_target(): validation method
    - _first_count(): helper method for counting results
    """
    
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
    ) -> dict[str, Any]:
        # Guardrails
        self._check_source_and_target(source_universe_id, new_universe_id, force)
        stories = stories or []
        arcs = arcs or []
        if dry_run:
            stories_cnt = self._first_count(
                self.repo.run(
                    "MATCH (:Universe {id:$src})-[:HAS_STORY]->(st:Story) WHERE size($stories)=0 OR st.id IN $stories RETURN count(DISTINCT st) AS c",
                    src=source_universe_id,
                    stories=stories,
                )
            )
            scenes_cnt = self._first_count(
                self.repo.run(
                    """
                MATCH (:Universe {id:$src})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
                WHERE (size($stories)=0 OR st.id IN $stories) AND ($scene_max IS NULL OR sc.sequence_index <= $scene_max)
                RETURN count(DISTINCT sc) AS c
                """,
                    src=source_universe_id,
                    stories=stories,
                    scene_max=scene_max_index,
                )
            )
            if include_all_entities:
                entities_cnt = self._first_count(
                    self.repo.run(
                        "MATCH (:Universe {id:$src})<-[:BELONGS_TO]-(e:Entity) RETURN count(DISTINCT e) AS c",
                        src=source_universe_id,
                    )
                )
            else:
                entities_cnt = self._first_count(
                    self.repo.run(
                        """
                    MATCH (:Universe {id:$src})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
                    WHERE (size($stories)=0 OR st.id IN $stories) AND ($scene_max IS NULL OR sc.sequence_index <= $scene_max)
                    MATCH (e:Entity)-[:APPEARS_IN]->(sc)
                    RETURN count(DISTINCT e) AS c
                    """,
                        src=source_universe_id,
                        stories=stories,
                        scene_max=scene_max_index,
                    )
                )
            facts_cnt = self._first_count(
                self.repo.run(
                    """
                MATCH (:Universe {id:$src})-[:HAS_STORY]->(st:Story)-[:HAS_SCENE]->(sc:Scene)
                WHERE (size($stories)=0 OR st.id IN $stories) AND ($scene_max IS NULL OR sc.sequence_index <= $scene_max)
                MATCH (f:Fact)-[:OCCURS_IN]->(sc)
                RETURN count(DISTINCT f) AS c
                """,
                    src=source_universe_id,
                    stories=stories,
                    scene_max=scene_max_index,
                )
            )
            sheets_cnt = self._first_count(
                self.repo.run(
                    "MATCH (:Universe {id:$src})<-[:BELONGS_TO]-(:Entity)-[:HAS_SHEET]->(sh:Sheet) RETURN count(DISTINCT sh) AS c",
                    src=source_universe_id,
                )
            )
            arcs_cnt = self._first_count(
                self.repo.run(
                    "MATCH (:Universe {id:$src})-[:HAS_ARC]->(a:Arc) WHERE size($arcs)=0 OR a.id IN $arcs RETURN count(DISTINCT a) AS c",
                    src=source_universe_id,
                    arcs=arcs,
                )
            )
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
