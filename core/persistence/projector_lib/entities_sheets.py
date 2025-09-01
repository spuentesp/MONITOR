from __future__ import annotations

from core.domain.entity import ConcreteEntity


class EntitiesSheetsMixin:
    def _upsert_entities_and_sheets(self, universe_id: str, entities: list[ConcreteEntity]):
        erows = []
        for e in entities:
            props = {
                "name": e.name,
                "type": e.type,
                "attributes": e.attributes,
                "universe_id": universe_id,
                "archetype_id": e.archetype_id,
            }
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
                props = {
                    "name": sh.name,
                    "type": sh.type,
                    "attributes": sh.attributes,
                    "story_id": sh.story_id,
                    "system_id": sh.system_id,
                }
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
            # Sheet USES_SYSTEM (optional)
            ssys_rows = [
                {"sid": sh.id, "sys": sh.system_id}
                for sh in e.sheets
                if getattr(sh, "system_id", None)
            ]
            if ssys_rows:
                self.repo.run(
                    """
                    UNWIND $rows AS row
                    MATCH (sh:Sheet {id: row.sid})
                    MATCH (sys:System {id: row.sys})
                    MERGE (sh)-[:USES_SYSTEM]->(sys)
                    """,
                    rows=ssys_rows,
                )

        # Entity USES_SYSTEM (optional)
        esys_rows = [
            {"eid": e.id, "sys": e.system_id} for e in entities if getattr(e, "system_id", None)
        ]
        if esys_rows:
            self.repo.run(
                """
                UNWIND $rows AS row
                MATCH (e:Entity {id: row.eid})
                MATCH (sys:System {id: row.sys})
                MERGE (e)-[:USES_SYSTEM]->(sys)
                """,
                rows=esys_rows,
            )
