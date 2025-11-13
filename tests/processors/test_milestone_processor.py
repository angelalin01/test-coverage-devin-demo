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
    
    def test_process_packet_failed_state_captures_error(self, processor):
        """Test that failed status captures error message."""
        packet = TelemetryPacket(
            packet_id="PKT-004",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="fuel_load",
            data={"status": "failed", "error": "Leak detected in fuel line"}
        )
        
        processor.process_packet(packet)
        
        status = processor.milestone_states["fuel_load"]
        assert status.state == MilestoneState.FAILED
        assert status.error_message == "Leak detected in fuel line"
    
    def test_process_packet_progress_only_triggers_in_progress(self, processor):
        """Test that progress field alone triggers IN_PROGRESS state."""
        packet = TelemetryPacket(
            packet_id="PKT-006",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="terminal_count",
            data={"progress": 45.5}
        )
        
        processor.process_packet(packet)
        
        status = processor.milestone_states["terminal_count"]
        assert status.state == MilestoneState.IN_PROGRESS
        assert status.progress_percent == 45.5
