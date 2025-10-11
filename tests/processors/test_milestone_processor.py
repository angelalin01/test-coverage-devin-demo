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
    
    def test_initialization(self, processor):
        """Test processor initializes with all milestones."""
        statuses = processor.get_all_statuses()
        assert len(statuses) == 6
        assert all(s.state == MilestoneState.NOT_STARTED for s in statuses.values())
    
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
    
    def test_process_packet_with_progress(self, processor):
        """Test processing packet with progress updates."""
        packet = TelemetryPacket(
            packet_id="PKT-002",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="fuel_load",
            data={"progress": 50.0, "flow_rate": 100.0}
        )
        
        processor.process_packet(packet)
        
        status = processor.get_milestone_status("fuel_load")
        assert status.progress_percent == 50.0
        assert status.state == MilestoneState.IN_PROGRESS
    
    def test_is_milestone_complete(self, processor):
        """Test checking if milestone is complete."""
        packet = TelemetryPacket(
            packet_id="PKT-005",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="terminal_count",
            data={"status": "complete"}
        )
        
        processor.process_packet(packet)
        assert processor.is_milestone_complete("terminal_count") is True
        assert processor.is_milestone_complete("ignition") is False
