import pytest
from datetime import datetime, timezone

from processors.milestone_processor import MilestoneProcessor, MilestoneState
from ingestion.packet import TelemetryPacket


class TestMilestoneProcessorPhase3:
    def test_is_milestone_complete_returns_true_for_complete(self):
        processor = MilestoneProcessor()
        
        complete_pkt = TelemetryPacket(
            packet_id="C1",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="ignition",
            data={"status": "complete"}
        )
        processor.process_packet(complete_pkt)
        
        assert processor.is_milestone_complete("ignition") is True

    def test_is_milestone_complete_returns_false_for_incomplete(self):
        processor = MilestoneProcessor()
        
        assert processor.is_milestone_complete("liftoff") is False
        
        in_progress_pkt = TelemetryPacket(
            packet_id="IP1",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="liftoff",
            data={"status": "in_progress"}
        )
        processor.process_packet(in_progress_pkt)
        
        assert processor.is_milestone_complete("liftoff") is False
