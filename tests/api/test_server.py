from datetime import datetime
from fastapi.testclient import TestClient

from api.server import create_app


def test_post_packets_happy_path():
    app = create_app()
    client = TestClient(app)
    payload = {
        "packet_id": "PKT-API-1",
        "timestamp": datetime.now().isoformat(),
        "source": "gs1",
        "milestone": "engine_chill",
        "data": {"status": "in_progress", "progress": 5},
    }
    resp = client.post("/packets", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "accepted"
    assert body["packet_id"] == "PKT-API-1"


def test_post_packets_invalid_returns_400():
    app = create_app()
    client = TestClient(app)
    payload = {
        "packet_id": "PKT-API-2",
        "timestamp": datetime.now().isoformat(),
        "source": "gs1",
        "milestone": "engine_chill",
        "data": {},  # invalid per validate_packet
    }
    resp = client.post("/packets", json=payload)
    assert resp.status_code == 400
    assert "Invalid packet data" in resp.text


def test_get_readiness_endpoint_returns_schema():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/readiness")
    assert resp.status_code == 200
    body = resp.json()
    assert "level" in body
    assert "overall_progress" in body
    assert "message" in body
