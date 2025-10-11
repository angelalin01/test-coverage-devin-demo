import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from api.server import create_app, StatusAPI, PacketSubmission


class TestStatusAPI:
    """Test cases for StatusAPI class."""
    
    @pytest.fixture
    def api(self):
        """Create a StatusAPI instance."""
        return StatusAPI()
    
    def test_initialization(self, api):
        """Test API initializes correctly."""
        assert api.receiver is not None
        assert api.processor is not None
        assert api.readiness_computer is not None
    
    def test_submit_packet(self, api):
        """Test submitting a valid packet."""
        packet_data = PacketSubmission(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"temperature": -180.5}
        )
        
        result = api.submit_packet(packet_data)
        assert result["status"] == "accepted"
        assert result["packet_id"] == "PKT-001"
    
    def test_get_milestone_status(self, api):
        """Test getting milestone status."""
        status = api.get_milestone_status("engine_chill")
        assert status is not None
        assert status.milestone == "engine_chill"
    
    def test_get_all_statuses(self, api):
        """Test getting all statuses."""
        statuses = api.get_all_statuses()
        assert len(statuses) == 6
    
    def test_get_readiness(self, api):
        """Test getting readiness status."""
        readiness = api.get_readiness()
        assert readiness is not None
        assert hasattr(readiness, 'level')
    
    def test_get_receiver_stats(self, api):
        """Test getting receiver statistics."""
        stats = api.get_receiver_stats()
        assert 'packet_count' in stats
        assert 'error_count' in stats


class TestFastAPIEndpoints:
    """Test cases for FastAPI endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        app = create_app()
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_submit_packet_endpoint(self, client):
        """Test packet submission endpoint."""
        packet_data = {
            "packet_id": "PKT-001",
            "timestamp": datetime.now().isoformat(),
            "source": "ground_station_1",
            "milestone": "engine_chill",
            "data": {"temperature": -180.5}
        }
        
        response = client.post("/packets", json=packet_data)
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"
    
    def test_get_all_milestones_endpoint(self, client):
        """Test getting all milestones endpoint."""
        response = client.get("/milestones")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 6
    
    def test_get_milestone_status_endpoint(self, client):
        """Test getting specific milestone endpoint."""
        response = client.get("/milestones/engine_chill")
        assert response.status_code == 200
        data = response.json()
        assert data["milestone"] == "engine_chill"
    
    def test_get_readiness_endpoint(self, client):
        """Test readiness endpoint."""
        response = client.get("/readiness")
        assert response.status_code == 200
        data = response.json()
        assert "level" in data
        assert "overall_progress" in data
    
    def test_get_stats_endpoint(self, client):
        """Test stats endpoint."""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "packet_count" in data
