from __future__ import annotations

from collections.abc import Iterable
import os

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase


class Neo4jRepo:
    def __init__(
        self, uri: str | None = None, user: str | None = None, password: str | None = None
    ):
        # Load env from .env if present (non-invasive)
        load_dotenv()
        self.uri = uri or os.getenv("NEO4J_URI")
        self.user = user or os.getenv("NEO4J_USER")
        self.password = password or os.getenv("NEO4J_PASS")
        self._driver: Driver | None = None

    def connect(self):
        if not self._driver:
            if not self.uri or not self.user or not self.password:
                raise ValueError(
                    "Missing Neo4j connection env. Set NEO4J_URI, NEO4J_USER, NEO4J_PASS."
                )
            # Add a short connection timeout so tests don't hang if Neo4j is unreachable
            try:
                self._driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password),
                    connection_timeout=3.0,  # seconds
                )
            except TypeError:
                # Older neo4j drivers may not accept connection_timeout; fall back
                self._driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        return self

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

    def run(self, cypher: str, **params):
        assert self._driver, "Driver not connected"
        with self._driver.session() as session:
            return list(session.run(cypher, **params))

    def ping(self) -> bool:
        try:
            self.run("RETURN 1 AS ok")
            return True
        except Exception:
            return False

    def bootstrap_constraints(self):
        constraints: Iterable[str] = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Omniverse) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Multiverse) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Universe) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Arc) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Story) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Scene) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Axiom) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Archetype) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Fact) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:RelationState) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:System) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Sheet) REQUIRE n.id IS UNIQUE",
        ]
        for c in constraints:
            self.run(c)

    def bootstrap_indexes(self):
        # Property indexes for frequently-filtered ids and sequence lookups
        indexes: Iterable[str] = [
            "CREATE INDEX IF NOT EXISTS FOR (s:Scene) ON (s.sequence_index)",
            "CREATE INDEX IF NOT EXISTS FOR (st:Story) ON (st.arc_id)",
            "CREATE INDEX IF NOT EXISTS FOR (sc:Scene) ON (sc.story_id)",
            "CREATE INDEX IF NOT EXISTS FOR ()-[hs:HAS_SCENE]-() ON (hs.sequence_index)",
        ]
        for i in indexes:
            self.run(i)
