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
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"status": "failed", "error": "Engine malfunction"}
        )
        processor.process_packet(packet)
        
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.SCRUBBED
        assert "engine_chill" in readiness.failed_milestones
        assert "Launch scrubbed" in readiness.message
    
    def test_partial_state_critical_ready(self, computer, processor):
        """Test PARTIAL state when critical milestones complete but others pending."""
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
        assert "pending" in readiness.message
    
    def test_not_ready_state(self, computer, processor):
        """Test NOT_READY state when critical milestones still pending."""
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="terminal_count",
            data={"status": "complete"}
        )
        processor.process_packet(packet)
        
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.NOT_READY
        assert "Not ready" in readiness.message
