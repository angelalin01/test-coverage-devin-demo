import pytest
from datetime import datetime

from processors.milestone_processor import MilestoneProcessor, MilestoneState
from ingestion.packet import TelemetryPacket


class TestMilestoneProcessor:
    """Test cases for MilestoneProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create a milestone processor instance."""
        return MilestoneProcessor()
    
    def test_process_packet_updates_state(self, processor):
        """Test processing packet updates milestone state."""
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"status": "in_progress", "temperature": -180.5}
        )
        
        result = processor.process_packet(packet)
        assert result is True
        
        status = processor.milestone_states["engine_chill"]
        assert status.state == MilestoneState.IN_PROGRESS
    
    def test_process_complete_milestone(self, processor):
        """Test marking milestone as complete."""
        packet = TelemetryPacket(
            packet_id="PKT-003",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="pressurization",
            data={"status": "complete", "final_pressure": 200.0}
        )
        
        processor.process_packet(packet)
        
        status = processor.milestone_states["pressurization"]
        assert status.state == MilestoneState.COMPLETE
        assert status.progress_percent == 100.0
    
    def test_get_all_statuses(self, processor):
        """Test get_all_statuses returns dict of all milestones."""
        all_statuses = processor.get_all_statuses()
        
        assert isinstance(all_statuses, dict)
        assert len(all_statuses) == 6
        assert "engine_chill" in all_statuses
        assert "fuel_load" in all_statuses
        assert all_statuses["engine_chill"].state == MilestoneState.NOT_STARTED
    
    def test_process_failed_milestone_with_error(self, processor):
        """Test processing failed milestone stores error message."""
        packet = TelemetryPacket(
            packet_id="PKT-FAIL",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"status": "failed", "error": "Temperature sensor malfunction"}
        )
        
        processor.process_packet(packet)
        
        status = processor.milestone_states["engine_chill"]
        assert status.state == MilestoneState.FAILED
        assert status.error_message == "Temperature sensor malfunction"
    
    def test_process_progress_only_update(self, processor):
        """Test progress-only update transitions NOT_STARTED to IN_PROGRESS."""
        packet = TelemetryPacket(
            packet_id="PKT-PROG",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="fuel_load",
            data={"progress": 25.5}
        )
        
        processor.process_packet(packet)
        
        status = processor.milestone_states["fuel_load"]
        assert status.state == MilestoneState.IN_PROGRESS
        assert status.progress_percent == 25.5
