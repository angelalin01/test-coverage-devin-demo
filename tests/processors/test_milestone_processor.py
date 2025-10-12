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
        
        status = processor.get_milestone_status("engine_chill")
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
        
        status = processor.get_milestone_status("pressurization")
        assert status.state == MilestoneState.COMPLETE
        assert status.progress_percent == 100.0
    
    def test_process_failed_milestone(self, processor):
        """Test processing failed milestone with error message."""
        packet = TelemetryPacket(
            packet_id="PKT-FAIL-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="fuel_load",
            data={"status": "failed", "error": "Fuel pump pressure anomaly detected"}
        )
        
        processor.process_packet(packet)
        
        status = processor.get_milestone_status("fuel_load")
        assert status.state == MilestoneState.FAILED
        assert status.error_message == "Fuel pump pressure anomaly detected"
    
    def test_progress_update_changes_state_to_in_progress(self, processor):
        """Test progress update transitions NOT_STARTED to IN_PROGRESS."""
        packet = TelemetryPacket(
            packet_id="PKT-PROG-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="terminal_count",
            data={"progress": 35.0, "countdown": 180}
        )
        
        processor.process_packet(packet)
        
        status = processor.get_milestone_status("terminal_count")
        assert status.state == MilestoneState.IN_PROGRESS
        assert status.progress_percent == 35.0
        assert status.metrics["countdown"] == 180.0
    
    def test_is_milestone_complete(self, processor):
        """Test checking if milestone is complete."""
        packet = TelemetryPacket(
            packet_id="PKT-COMPLETE",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"status": "complete"}
        )
        
        processor.process_packet(packet)
        assert processor.is_milestone_complete("engine_chill") is True
        assert processor.is_milestone_complete("fuel_load") is False
