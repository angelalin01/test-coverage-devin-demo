import pytest
from datetime import datetime

from status.readiness import ReadinessComputer, ReadinessLevel
from processors.milestone_processor import MilestoneProcessor, MilestoneState
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
    
    def test_initialization(self, computer, processor):
        """Test readiness computer initializes correctly."""
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.NOT_READY
        assert len(readiness.pending_milestones) == 6
    
    def test_not_ready_state(self, computer, processor):
        """Test NOT_READY state when critical milestones incomplete."""
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.NOT_READY
    
    def test_partial_readiness(self, computer, processor):
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
    
    def test_hold_state_non_critical_failure(self, computer, processor):
        """Test HOLD state for non-critical milestone failure."""
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="terminal_count",
            data={"status": "failed", "error": "Timer malfunction"}
        )
        processor.process_packet(packet)
        
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.HOLD
        assert "terminal_count" in readiness.failed_milestones
    
    def test_scrubbed_state_critical_failure(self, computer, processor):
        """Test SCRUBBED state for critical milestone failure."""
        packet = TelemetryPacket(
            packet_id="PKT-002",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"status": "failed", "error": "Cooling system failure"}
        )
        processor.process_packet(packet)
        
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.SCRUBBED
        assert "engine_chill" in readiness.failed_milestones
    
    def test_is_go_for_launch(self, computer, processor):
        """Test is_go_for_launch returns correct status."""
        assert computer.is_go_for_launch() is False
        
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
        
        assert computer.is_go_for_launch() is True
    
    def test_get_blocking_issues(self, computer, processor):
        """Test getting blocking issues."""
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="fuel_load",
            data={"status": "failed", "error": "Fuel leak detected"}
        )
        processor.process_packet(packet)
        
        issues = computer.get_blocking_issues()
        assert len(issues) > 0
        assert any("fuel_load" in issue for issue in issues)
