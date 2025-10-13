from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from api.server import create_app

def make_client():
    app = create_app()
    return TestClient(app)

def test_post_packets_201_and_readiness_get_200():
    client = make_client()
    payload = {
        "packet_id": "PKT-INTEG-1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "gs",
        "milestone": "engine_chill",
        "data": {"status": "in_progress"}
    }
    r = client.post("/packets", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "accepted"
    gr = client.get("/readiness")
    assert gr.status_code == 200
    rb = gr.json()
    assert "level" in rb and "overall_progress" in rb

def test_post_packets_400_invalid_packet():
    client = make_client()
    payload = {
        "packet_id": "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "gs",
        "milestone": "engine_chill",
        "data": {"status": "in_progress"}
    }
    r = client.post("/packets", json=payload)
    assert r.status_code == 400

def test_post_packets_422_invalid_schema():
    client = make_client()
    r = client.post("/packets", json={"packet_id": "X"})
    assert r.status_code == 422
