import pytest
from datetime import datetime, timezone

from processors.milestone_processor import MilestoneProcessor, MilestoneState
from status.readiness import ReadinessComputer, ReadinessLevel
from ingestion.packet import TelemetryPacket


class TestReadinessPhase3:
    def test_scrubbed_state_when_critical_milestone_fails(self):
        processor = MilestoneProcessor()
        computer = ReadinessComputer(processor)
        
        fail_pkt = TelemetryPacket(
            packet_id="CRIT-FAIL",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="engine_chill",
            data={"status": "failed", "error": "cryogenic leak"}
        )
        processor.process_packet(fail_pkt)
        
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.SCRUBBED
        assert "engine_chill" in readiness.failed_milestones
        assert "scrubbed due to critical failures" in readiness.message.lower()
        assert "engine_chill" in readiness.message

    def test_hold_state_when_noncritical_milestone_fails(self):
        processor = MilestoneProcessor()
        computer = ReadinessComputer(processor)
        
        complete_critical = TelemetryPacket(
            packet_id="C1",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="engine_chill",
            data={"status": "complete"}
        )
        processor.process_packet(complete_critical)
        
        fail_noncritical = TelemetryPacket(
            packet_id="F1",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="terminal_count",
            data={"status": "failed", "error": "sensor malfunction"}
        )
        processor.process_packet(fail_noncritical)
        
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.HOLD
        assert "terminal_count" in readiness.failed_milestones
        assert "hold" in readiness.message.lower()
        assert "terminal_count" in readiness.message

    def test_not_ready_when_critical_milestones_pending(self):
        processor = MilestoneProcessor()
        computer = ReadinessComputer(processor)
        
        in_progress_pkt = TelemetryPacket(
            packet_id="IP1",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="fuel_load",
            data={"status": "in_progress", "progress": 30.0}
        )
        processor.process_packet(in_progress_pkt)
        
        readiness = computer.compute_readiness()
        assert readiness.level == ReadinessLevel.NOT_READY
        assert "fuel_load" in readiness.pending_milestones
        assert "not ready" in readiness.message.lower()
        assert "pending" in readiness.message.lower()
