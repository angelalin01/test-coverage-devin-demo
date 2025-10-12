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
    
    def test_not_ready_state_initial(self, computer):
        """Test NOT_READY state when no critical milestones are complete."""
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.NOT_READY
        assert readiness.overall_progress == 0.0
        assert len(readiness.ready_milestones) == 0
    
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
    
    def test_scrubbed_state_critical_failure(self, computer, processor):
        """Test SCRUBBED state when critical milestone fails."""
        packet = TelemetryPacket(
            packet_id="PKT-CRIT-FAIL",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="fuel_load",
            data={"status": "failed", "error": "Critical fuel system failure"}
        )
        processor.process_packet(packet)
        
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.SCRUBBED
        assert "fuel_load" in readiness.failed_milestones
        assert "scrubbed" in readiness.message.lower()
        assert "fuel_load" in readiness.message
    
    def test_hold_state_non_critical_failure(self, computer, processor):
        """Test HOLD state when non-critical milestone fails."""
        packet = TelemetryPacket(
            packet_id="PKT-NON-CRIT-FAIL",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="terminal_count",
            data={"status": "failed", "error": "Communication glitch"}
        )
        processor.process_packet(packet)
        
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.HOLD
        assert "terminal_count" in readiness.failed_milestones
        assert "hold" in readiness.message.lower()
    
    def test_partial_readiness(self, computer, processor):
        """Test PARTIAL readiness when critical milestones complete but others pending."""
        critical_milestones = ["engine_chill", "fuel_load", "pressurization"]
        
        for milestone in critical_milestones:
            packet = TelemetryPacket(
                packet_id=f"PKT-{milestone}",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone=milestone,
                data={"status": "complete"}
            )
            processor.process_packet(packet)
        
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.PARTIAL
        assert len(readiness.ready_milestones) == 3
        assert len(readiness.pending_milestones) == 3
