import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from api.server import create_app


class TestStatusAPI:
    """Test cases for StatusAPI endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a FastAPI test client."""
        app = create_app()
        return TestClient(app)
    
    def test_submit_packet_success(self, client):
        """Test successful packet submission."""
        response = client.post("/packets", json={
            "packet_id": "PKT-001",
            "timestamp": datetime.now().isoformat(),
            "source": "ground_station_1",
            "milestone": "engine_chill",
            "data": {"temperature": -180.5, "status": "in_progress"}
        })
        
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"
        assert response.json()["packet_id"] == "PKT-001"
    
    def test_get_readiness_endpoint(self, client):
        """Test GET /readiness endpoint."""
        response = client.get("/readiness")
        
        assert response.status_code == 200
        result = response.json()
        assert "level" in result
        assert "overall_progress" in result
        assert "ready_milestones" in result
        assert "pending_milestones" in result
