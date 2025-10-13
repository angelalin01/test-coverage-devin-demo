from datetime import datetime

from processors.milestone_processor import MilestoneProcessor, MilestoneState
from ingestion.packet import TelemetryPacket


class TestProgressAndMetrics:
    def test_progress_only_moves_to_in_progress(self):
        proc = MilestoneProcessor()
        pkt = TelemetryPacket(
            packet_id="PKT-PROG",
            timestamp=datetime.now(),
            source="gs1",
            milestone="fuel_load",
            data={"progress": 10, "status": "in_progress"},
        )

        assert proc.process_packet(pkt) is True
        status = proc.milestone_states["fuel_load"]
        assert status is not None
        assert status.state in (MilestoneState.IN_PROGRESS,)
        assert status.progress_percent == 10.0
