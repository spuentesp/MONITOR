from __future__ import annotations

import sys

from dotenv import load_dotenv


def _status(ok: bool) -> str:
    return "OK" if ok else "FAIL"


def check_neo4j() -> bool:
    try:
        from core.persistence.neo4j_repo import Neo4jRepo

        load_dotenv()
        repo = Neo4jRepo().connect()
        return repo.ping()
    except Exception:
        return False


def check_mongo() -> bool:
    try:
        from core.persistence.mongo_store import MongoStore

        load_dotenv()
        store = MongoStore().connect()
        return store.ping()
    except Exception:
        return False


def check_qdrant() -> bool:
    try:
        from core.persistence.qdrant_index import QdrantIndex

        load_dotenv()
        idx = QdrantIndex().connect()
        return idx.ping()
    except Exception:
        return False


def check_opensearch() -> bool:
    try:
        from core.persistence.search_index import SearchIndex

        load_dotenv()
        s = SearchIndex().connect()
        return s.ping()
    except Exception:
        return False


def check_minio() -> bool:
    try:
        from core.persistence.object_store import ObjectStore

        load_dotenv()
        s = ObjectStore().connect()
        return s.ping()
    except Exception:
        return False


def main(argv: list[str]) -> int:
    load_dotenv()
    results: dict[str, bool] = {
        "neo4j": check_neo4j(),
        "mongo": check_mongo(),
        "qdrant": check_qdrant(),
        "opensearch": check_opensearch(),
        "minio": check_minio(),
    }
    for name, ok in results.items():
        print(f"{name}: {_status(ok)}")
    rc = 0 if all(results.values()) else 2
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
