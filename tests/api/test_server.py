import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from api.server import create_app


@pytest.fixture
def client():
    """Create a test client for the API."""
    app = create_app()
    return TestClient(app)


def test_submit_packet_success(client):
    """Test submitting a valid packet via POST /packets."""
    packet_data = {
        "packet_id": "PKT-API-001",
        "timestamp": datetime.now().isoformat(),
        "source": "ground_station_1",
        "milestone": "engine_chill",
        "data": {"temperature": -180.5}
    }
    
    response = client.post("/packets", json=packet_data)
    assert response.status_code == 201
    assert response.json()["status"] == "accepted"
    assert response.json()["packet_id"] == "PKT-API-001"


def test_submit_packet_invalid_data(client):
    """Test submitting invalid packet returns 400 error."""
    packet_data = {
        "packet_id": "PKT-API-002",
        "timestamp": datetime.now().isoformat(),
        "source": "ground_station_1",
        "milestone": "engine_chill",
        "data": {}
    }
    
    response = client.post("/packets", json=packet_data)
    assert response.status_code == 400
    assert "Invalid packet data" in response.json()["detail"]


def test_get_readiness_initial_state(client):
    """Test GET /readiness returns NOT_READY initially."""
    response = client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == "not_ready"
    assert data["overall_progress"] == 0.0


def test_get_readiness_after_packets(client):
    """Test GET /readiness updates after processing packets."""
    packet_data = {
        "packet_id": "PKT-API-003",
        "timestamp": datetime.now().isoformat(),
        "source": "ground_station_1",
        "milestone": "engine_chill",
        "data": {"status": "complete"}
    }
    
    client.post("/packets", json=packet_data)
    
    response = client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert len(data["ready_milestones"]) == 1
    assert "engine_chill" in data["ready_milestones"]


def test_integration_full_workflow(client):
    """Test complete workflow: submit multiple packets and check readiness progression."""
    milestones = ["engine_chill", "fuel_load", "pressurization"]
    
    for milestone in milestones:
        packet_data = {
            "packet_id": f"PKT-{milestone}",
            "timestamp": datetime.now().isoformat(),
            "source": "ground_station_1",
            "milestone": milestone,
            "data": {"status": "complete"}
        }
        response = client.post("/packets", json=packet_data)
        assert response.status_code == 201
    
    readiness_response = client.get("/readiness")
    data = readiness_response.json()
    assert data["level"] == "partial"
    assert len(data["ready_milestones"]) == 3
    assert len(data["pending_milestones"]) == 3
