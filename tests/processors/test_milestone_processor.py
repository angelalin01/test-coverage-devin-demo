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
        """Test processing a milestone that has failed."""
        packet = TelemetryPacket(
            packet_id="PKT-004",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="pressurization",
            data={"status": "failed", "error": "Pressure sensor malfunction"}
        )
        
        result = processor.process_packet(packet)
        
        assert result is True
        status = processor.get_milestone_status("pressurization")
        assert status.state == MilestoneState.FAILED
        assert status.error_message == "Pressure sensor malfunction"
    
    def test_process_failed_milestone_without_error_message(self, processor):
        """Test processing a failed milestone without explicit error message."""
        packet = TelemetryPacket(
            packet_id="PKT-005",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="terminal_count",
            data={"status": "failed"}
        )
        
        result = processor.process_packet(packet)
        
        assert result is True
        status = processor.get_milestone_status("terminal_count")
        assert status.state == MilestoneState.FAILED
        assert status.error_message == "Unknown error"
    
    @pytest.mark.parametrize("milestone,status_value,error_msg", [
        ("ignition", "failed", "Engine ignition failure"),
        ("liftoff", "failed", "Launch abort"),
    ])
    def test_failed_milestone_transitions(self, processor, milestone, status_value, error_msg):
        """Test failed milestone state transitions."""
        packet = TelemetryPacket(
            packet_id="PKT-006",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone=milestone,
            data={"status": status_value, "error": error_msg}
        )
        
        result = processor.process_packet(packet)
        
        assert result is True
        status = processor.get_milestone_status(milestone)
        assert status.state == MilestoneState.FAILED
        assert status.error_message == error_msg
    
    def test_process_packet_with_metrics(self, processor):
        """Test processing packet updates metrics dictionary."""
        packet = TelemetryPacket(
            packet_id="PKT-008",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="fuel_load",
            data={"temperature": 25.5, "pressure": 101.3, "flow_rate": 100.0}
        )
        
        processor.process_packet(packet)
        
        status = processor.get_milestone_status("fuel_load")
        assert "temperature" in status.metrics
        assert "pressure" in status.metrics
        assert "flow_rate" in status.metrics
        assert status.metrics["temperature"] == 25.5
    
    def test_process_packet_with_progress_updates_state(self, processor):
        """Test that progress updates state from NOT_STARTED to IN_PROGRESS."""
        packet = TelemetryPacket(
            packet_id="PKT-009",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"progress": 50.0}
        )
        
        processor.process_packet(packet)
        
        status = processor.get_milestone_status("engine_chill")
        assert status.state == MilestoneState.IN_PROGRESS
        assert status.progress_percent == 50.0
    
    def test_is_milestone_complete(self, processor):
        """Test is_milestone_complete method returns correct status."""
        packet = TelemetryPacket(
            packet_id="PKT-500",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="pressurization",
            data={"status": "complete"}
        )
        processor.process_packet(packet)
        
        assert processor.is_milestone_complete("pressurization") is True
        assert processor.is_milestone_complete("engine_chill") is False
