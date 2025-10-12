import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from api.server import create_app, StatusAPI, PacketSubmission
from processors.milestone_processor import MilestoneState
from status.readiness import ReadinessLevel


class TestServerAPI:
    """Test cases for FastAPI server endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_submit_packet_endpoint(self, client):
        """Test POST /packets endpoint accepts valid packet."""
        packet_data = {
            "packet_id": "PKT-API-001",
            "timestamp": datetime.now().isoformat(),
            "source": "ground_station_1",
            "milestone": "engine_chill",
            "data": {"temperature": -180.5, "status": "in_progress"}
        }
        
        response = client.post("/packets", json=packet_data)
        
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"
        assert response.json()["packet_id"] == "PKT-API-001"
    
    def test_submit_invalid_packet_returns_400(self, client):
        """Test POST /packets rejects invalid packet."""
        packet_data = {
            "packet_id": "",
            "timestamp": datetime.now().isoformat(),
            "source": "ground_station_1",
            "milestone": "engine_chill",
            "data": {}
        }
        
        response = client.post("/packets", json=packet_data)
        assert response.status_code == 400
    
    def test_get_milestone_endpoint(self, client):
        """Test GET /milestones/{milestone} returns milestone status."""
        packet_data = {
            "packet_id": "PKT-API-002",
            "timestamp": datetime.now().isoformat(),
            "source": "ground_station_1",
            "milestone": "pressurization",
            "data": {"status": "complete"}
        }
        client.post("/packets", json=packet_data)
        
        response = client.get("/milestones/pressurization")
        
        assert response.status_code == 200
        data = response.json()
        assert data["milestone"] == "pressurization"
        assert data["state"] == MilestoneState.COMPLETE.value
    
    def test_get_milestone_not_found(self, client):
        """Test GET /milestones/{milestone} returns 404 for unknown milestone."""
        response = client.get("/milestones/nonexistent_milestone")
        assert response.status_code == 404
    
    def test_get_all_milestones_endpoint(self, client):
        """Test GET /milestones returns all milestone statuses."""
        response = client.get("/milestones")
        
        assert response.status_code == 200
        data = response.json()
        assert "engine_chill" in data
        assert "fuel_load" in data
        assert len(data) == 6
    
    def test_get_readiness_endpoint(self, client):
        """Test GET /readiness returns launch readiness."""
        response = client.get("/readiness")
        
        assert response.status_code == 200
        data = response.json()
        assert "level" in data
        assert "overall_progress" in data
        assert data["level"] in [level.value for level in ReadinessLevel]
    
    def test_health_check_endpoint(self, client):
        """Test GET /health returns healthy status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_get_receiver_stats(self):
        """Test StatusAPI.get_receiver_stats returns receiver statistics."""
        api = StatusAPI()
        
        packet_data = PacketSubmission(
            packet_id="PKT-STATS-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="fuel_load",
            data={"status": "in_progress"}
        )
        api.submit_packet(packet_data)
        
        stats = api.get_receiver_stats()
        
        assert 'packet_count' in stats
        assert 'error_count' in stats
        assert 'buffer_size' in stats
        assert 'buffer_capacity' in stats
        assert stats['packet_count'] >= 1
