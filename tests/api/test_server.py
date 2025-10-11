import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from api.server import create_app, StatusAPI
from ingestion.packet import TelemetryPacket
from processors.milestone_processor import MilestoneState


class TestStatusAPI:
    
    @pytest.fixture
    def api(self):
        return StatusAPI()
    
    def test_initialization(self, api):
        assert api.receiver is not None
        assert api.processor is not None
        assert api.readiness_computer is not None
        assert api.aggregator is not None
    
    def test_submit_packet_success(self, api):
        packet_data = {
            "packet_id": "PKT-001",
            "timestamp": datetime.now().isoformat(),
            "source": "ground_station_1",
            "milestone": "engine_chill",
            "data": {"temperature": -180.5, "status": "in_progress"}
        }
        
        from api.server import PacketSubmission
        submission = PacketSubmission(**packet_data)
        result = api.submit_packet(submission)
        
        assert result["status"] == "accepted"
        assert result["packet_id"] == "PKT-001"
    
    def test_submit_packet_invalid_data(self, api):
        from fastapi import HTTPException
        from api.server import PacketSubmission
        
        packet_data = {
            "packet_id": "PKT-002",
            "timestamp": datetime.now().isoformat(),
            "source": "ground_station_1",
            "milestone": "fuel_load",
            "data": {}
        }
        
        submission = PacketSubmission(**packet_data)
        
        with pytest.raises(HTTPException) as exc_info:
            api.submit_packet(submission)
        
        assert exc_info.value.status_code == 400
        assert "Invalid packet data" in exc_info.value.detail
    
    def test_get_milestone_status(self, api):
        packet = TelemetryPacket(
            packet_id="PKT-003",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="pressurization",
            data={"status": "in_progress", "pressure": 150.0}
        )
        api.processor.process_packet(packet)
        
        status = api.get_milestone_status("pressurization")
        assert status.state == MilestoneState.IN_PROGRESS
        assert status.milestone == "pressurization"
    
    def test_get_milestone_not_found(self, api):
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            api.get_milestone_status("invalid_milestone")
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail
    
    def test_get_all_statuses(self, api):
        statuses = api.get_all_statuses()
        assert len(statuses) == 6
        assert "engine_chill" in statuses
        assert "liftoff" in statuses
    
    def test_get_readiness(self, api):
        readiness = api.get_readiness()
        assert readiness.level is not None
        assert readiness.overall_progress >= 0.0
    
    def test_get_receiver_stats(self, api):
        stats = api.get_receiver_stats()
        assert "packet_count" in stats
        assert "error_count" in stats
        assert "buffer_size" in stats
    
    def test_callback_integration(self, api):
        packet = TelemetryPacket(
            packet_id="PKT-004",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="terminal_count",
            data={"status": "complete"}
        )
        
        api.receiver.receive_packet(packet)
        
        status = api.processor.get_milestone_status("terminal_count")
        assert status.state == MilestoneState.COMPLETE
