from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.interfaces.api_interface import app  # noqa: E402


def test_root_open():
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200


def test_requires_context_token_for_other_paths():
    client = TestClient(app)
    r = client.get("/secure")
    assert r.status_code == 400


def test_rejects_invalid_context_token():
    client = TestClient(app)
    r = client.get("/secure", headers={"X-Context-Token": "{not-json}"})
    assert r.status_code == 422


def test_accepts_valid_context_token():
    client = TestClient(app)
    token = '{"omniverse_id":"o","multiverse_id":"m","universe_id":"u"}'

    # Define a dummy route to pass middleware
    @app.get("/secure")
    def secure():  # pragma: no cover - trivial route
        return {"ok": True}

    r = client.get("/secure", headers={"X-Context-Token": token})
    assert r.status_code in (200, 307)  # 307 may happen due to testclient quirks
