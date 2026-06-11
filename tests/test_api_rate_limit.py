import pytest

try:
    from fastapi.testclient import TestClient
    from api import build_app
    HAVE = True
except Exception:
    HAVE = False

pytestmark = pytest.mark.skipif(not HAVE, reason="fastapi not installed")


def test_disabled_rate_limit_never_429s():
    client = TestClient(build_app(rate_limit=False))
    for _ in range(80):
        r = client.post("/ask", json={"character": "park", "question": "ping"})
        assert r.status_code == 200, r.text


def test_enabled_rate_limit_eventually_429s():
    client = TestClient(build_app(rate_limit=True))
    denied = 0
    for _ in range(100):
        r = client.post("/ask", json={"character": "park", "question": "ping"})
        if r.status_code == 429:
            denied += 1
    assert denied > 0, "expected some 429 responses with rate_limit=True"
