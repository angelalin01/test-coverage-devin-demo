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
    
    def test_scrubbed_state_on_critical_failure(self, computer, processor):
        """Test SCRUBBED state when a critical milestone fails."""
        critical_milestones = ["engine_chill", "fuel_load", "pressurization"]
        
        for milestone in critical_milestones[:2]:
            packet = TelemetryPacket(
                packet_id=f"PKT-{milestone}",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone=milestone,
                data={"status": "complete"}
            )
            processor.process_packet(packet)
        
        fail_packet = TelemetryPacket(
            packet_id="PKT-pressurization",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="pressurization",
            data={"status": "failed", "error": "Critical system failure"}
        )
        processor.process_packet(fail_packet)
        
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.SCRUBBED
        assert "pressurization" in readiness.failed_milestones
        assert "scrubbed" in readiness.message.lower()
    
    def test_hold_state_on_non_critical_failure(self, computer, processor):
        """Test HOLD state when a non-critical milestone fails."""
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
        
        fail_packet = TelemetryPacket(
            packet_id="PKT-ignition",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="ignition",
            data={"status": "failed", "error": "Ignition sequence aborted"}
        )
        processor.process_packet(fail_packet)
        
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.HOLD
        assert "ignition" in readiness.failed_milestones
        assert "hold" in readiness.message.lower()
