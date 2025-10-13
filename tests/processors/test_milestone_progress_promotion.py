from datetime import datetime
from processors.milestone_processor import MilestoneProcessor, MilestoneState
from ingestion.packet import TelemetryPacket

def test_progress_only_promotes_not_started_to_in_progress():
    proc = MilestoneProcessor()
    pkt = TelemetryPacket(
        packet_id="PKT-PROG-1",
        timestamp=datetime.utcnow(),
        source="gs",
        milestone="terminal_count",
        data={"progress": 10.0}
    )
    assert proc.process_packet(pkt) is True
    status = proc.get_all_statuses()["terminal_count"]
    assert status.state == MilestoneState.IN_PROGRESS
    assert status.progress_percent == 10.0
    assert status.last_update == pkt.timestamp
