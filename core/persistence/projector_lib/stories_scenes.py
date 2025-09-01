from __future__ import annotations

from core.domain.story import Story


class StoriesScenesMixin:
    def _upsert_stories_and_scenes(self, universe_id: str, stories: list[Story]) -> None:
        # Stories
        srows = []
        for s in stories:
            props = {
                "title": s.title,
                "summary": s.summary,
                "universe_id": universe_id,
                "arc_id": s.arc_id,
            }
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
        # Story USES_SYSTEM (optional, overrides universe scope while active)
        ssys_rows = [
            {"sid": s.id, "sys": s.system_id} for s in stories if getattr(s, "system_id", None)
        ]
        if ssys_rows:
            self.repo.run(
                """
                UNWIND $rows AS row
                MATCH (st:Story {id: row.sid})
                MATCH (sys:System {id: row.sys})
                MERGE (st)-[:USES_SYSTEM]->(sys)
                """,
                rows=ssys_rows,
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
            rows=[
                {"id": s.id, "props": {"arc_id": s.arc_id}, "seq": idx + 1}
                for idx, s in enumerate(stories)
            ],
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

    def _upsert_appears_in(self, stories: list[Story]) -> None:
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
