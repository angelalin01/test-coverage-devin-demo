from fastapi.testclient import TestClient
from api.server import create_app, PacketSubmission
from datetime import datetime

def test_create_app_and_get_readiness_default():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/readiness")
    assert resp.status_code == 200
    body = resp.json()
    assert "level" in body
    assert "overall_progress" in body

def test_post_packets_valid_201():
    app = create_app()
    client = TestClient(app)
    payload = {
        "packet_id": "PKT-API-001",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "ground_station_1",
        "milestone": "engine_chill",
        "data": {"status": "in_progress"}
    }
    resp = client.post("/packets", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "accepted"
    assert body["packet_id"] == "PKT-API-001"
