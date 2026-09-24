from fastapi.testclient import TestClient

from solaris import __version__
from solaris.api import app


def test_health_ok():
    resp = TestClient(app).get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "version": __version__}
