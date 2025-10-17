import pytest
from datetime import datetime

from status.readiness import ReadinessComputer, ReadinessLevel
from processors.milestone_processor import MilestoneProcessor
from ingestion.packet import TelemetryPacket
from tests.test_utils import create_test_packet


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
    
    def test_partial_readiness_state(self, computer, processor):
        """Test PARTIAL state when critical milestones ready but others pending."""
        critical_milestones = ["engine_chill", "fuel_load", "pressurization"]
        
        for milestone in critical_milestones:
            packet = create_test_packet(
                packet_id=f"PKT-{milestone}",
                milestone=milestone,
                data={"status": "complete"}
            )
            processor.process_packet(packet)
        
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.PARTIAL
        assert len(readiness.ready_milestones) == 3
        assert len(readiness.pending_milestones) == 3
        assert "pending" in readiness.message.lower()
    
    def test_not_ready_state(self, computer, processor):
        """Test NOT_READY state when no critical milestones ready."""
        non_critical = ["terminal_count", "ignition"]
        
        for milestone in non_critical:
            packet = create_test_packet(
                packet_id=f"PKT-{milestone}",
                milestone=milestone,
                data={"status": "complete"}
            )
            processor.process_packet(packet)
        
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.NOT_READY
        assert len(readiness.ready_milestones) == 2
        assert len(readiness.pending_milestones) == 4
        assert "not ready" in readiness.message.lower()
