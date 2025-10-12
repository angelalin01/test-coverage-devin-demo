from datetime import datetime, timezone
from processors.milestone_processor import MilestoneProcessor, MilestoneState
from ingestion.packet import TelemetryPacket


class TestMilestoneProcessorPhase1:
    def test_progress_bumps_state_from_not_started_to_in_progress(self):
        proc = MilestoneProcessor()
        pkt = TelemetryPacket(
            packet_id="P1",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="engine_chill",
            data={"progress": 5.0}
        )
        assert proc.process_packet(pkt) is True
        st = proc.get_all_statuses()["engine_chill"]
        assert st.state == MilestoneState.IN_PROGRESS
        assert st.progress_percent == 5.0

    def test_failed_sets_error_message(self):
        proc = MilestoneProcessor()
        pkt = TelemetryPacket(
            packet_id="P2",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="fuel_load",
            data={"status": "failed", "error": "pressure drop"}
        )
        assert proc.process_packet(pkt) is True
        st = proc.get_all_statuses()["fuel_load"]
        assert st.state == MilestoneState.FAILED
        assert st.error_message == "pressure drop"

    def test_in_progress_to_complete_updates_progress_100(self):
        proc = MilestoneProcessor()
        pkt1 = TelemetryPacket(
            packet_id="P3a",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="pressurization",
            data={"status": "in_progress", "progress": 50.0}
        )
        pkt2 = TelemetryPacket(
            packet_id="P3b",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="pressurization",
            data={"status": "complete"}
        )
        assert proc.process_packet(pkt1) is True
        assert proc.process_packet(pkt2) is True
        st = proc.get_all_statuses()["pressurization"]
        assert st.state == MilestoneState.COMPLETE
        assert st.progress_percent == 100.0
