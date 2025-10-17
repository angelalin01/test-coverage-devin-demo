import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from api.server import create_app


class TestStatusAPI:
    """Test cases for StatusAPI endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        app = create_app()
        return TestClient(app, raise_server_exceptions=False)
    
    def test_submit_packet_success(self, client):
        """Test successful packet submission."""
        response = client.post("/packets", json={
            "packet_id": "PKT-001",
            "timestamp": "2024-10-17T10:00:00",
            "source": "ground_station_1",
            "milestone": "engine_chill",
            "data": {"status": "in_progress"}
        })
        
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"
        assert response.json()["packet_id"] == "PKT-001"
    
    def test_submit_packet_empty_packet_id(self, client):
        """Test packet submission with empty packet_id triggers validation error."""
        response = client.post("/packets", json={
            "packet_id": "",
            "timestamp": "2024-10-17T10:00:00",
            "source": "ground_station_1",
            "milestone": "engine_chill",
            "data": {"status": "in_progress"}
        })
        
        assert response.status_code == 400
        assert "Invalid packet data" in response.json()["detail"]
    
    def test_get_readiness_initial_state(self, client):
        """Test readiness endpoint returns initial NOT_READY state."""
        response = client.get("/readiness")
        
        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "not_ready"
        assert len(data["pending_milestones"]) == 6
        assert len(data["ready_milestones"]) == 0
    
    def test_get_readiness_after_packet_submission(self, client):
        """Test readiness reflects submitted packet state."""
        client.post("/packets", json={
            "packet_id": "PKT-001",
            "timestamp": "2024-10-17T10:00:00",
            "source": "ground_station_1",
            "milestone": "engine_chill",
            "data": {"status": "complete"}
        })
        
        response = client.get("/readiness")
        
        assert response.status_code == 200
        data = response.json()
        assert "engine_chill" in data["ready_milestones"]
