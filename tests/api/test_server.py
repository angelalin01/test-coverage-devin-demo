import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from api.server import create_app


class TestAPIEndpoints:
    """Test cases for API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        app = create_app()
        return TestClient(app)
    
    def test_submit_valid_packet(self, client):
        """Test POST /packets with valid packet returns 201."""
        packet_data = {
            "packet_id": "PKT-001",
            "timestamp": datetime.now().isoformat(),
            "source": "ground_station_1",
            "milestone": "engine_chill",
            "data": {"status": "in_progress", "temperature": -180.5}
        }
        
        response = client.post("/packets", json=packet_data)
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"
        assert response.json()["packet_id"] == "PKT-001"
    
    def test_get_readiness(self, client):
        """Test GET /readiness returns proper structure."""
        response = client.get("/readiness")
        assert response.status_code == 200
        
        data = response.json()
        assert "level" in data
        assert "ready_milestones" in data
        assert "pending_milestones" in data
        assert "failed_milestones" in data
        assert "overall_progress" in data
        assert "message" in data
