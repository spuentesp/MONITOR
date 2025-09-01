from __future__ import annotations

import os
from typing import Iterable
from neo4j import GraphDatabase, Driver


class Neo4jRepo:
    def __init__(self, uri: str | None = None, user: str | None = None, password: str | None = None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASS", "neo4jpass")
        self._driver: Driver | None = None

    def connect(self):
        if not self._driver:
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
