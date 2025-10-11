import pytest
from datetime import datetime

from status.readiness import ReadinessComputer, ReadinessLevel
from processors.milestone_processor import MilestoneProcessor
from ingestion.packet import TelemetryPacket


class TestReadinessComputer:
    """Test cases for ReadinessComputer class."""
    
    @pytest.fixture
    def processor(self):
        """Create a milestone processor."""
        return MilestoneProcessor()
    
    @pytest.fixture
    def computer(self, processor):
        """Create a readiness computer."""
        return ReadinessComputer(processor)
    
    def test_initialization(self, computer):
        """Test readiness computer initializes correctly."""
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.NOT_READY
        assert len(readiness.pending_milestones) == 6
    
    def test_ready_state(self, computer, processor):
        """Test READY state when all milestones complete."""
        all_milestones = ["engine_chill", "fuel_load", "pressurization", 
                         "terminal_count", "ignition", "liftoff"]
        
        for milestone in all_milestones:
            packet = TelemetryPacket(
                packet_id=f"PKT-{milestone}",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone=milestone,
                data={"status": "complete"}
            )
            processor.process_packet(packet)
        
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.READY
        assert readiness.overall_progress == 100.0
