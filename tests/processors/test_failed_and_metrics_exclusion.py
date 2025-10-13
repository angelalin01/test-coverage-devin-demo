from datetime import datetime

from processors.milestone_processor import MilestoneProcessor, MilestoneState
from ingestion.packet import TelemetryPacket


def test_failed_sets_error_message_and_state_failed():
    proc = MilestoneProcessor()
    pkt = TelemetryPacket(
        packet_id="PKT-F",
        timestamp=datetime.now(),
        source="gs1",
        milestone="fuel_load",
        data={"status": "failed", "error": "sensor_fault", "status_dup": "ignored"},
    )
    ok = proc.process_packet(pkt)
    assert ok is True
    status = proc.milestone_states["fuel_load"]
    assert status.state == MilestoneState.FAILED
    assert status.error_message == "sensor_fault"


def test_metrics_fields_not_added_for_status_progress_keys():
    proc = MilestoneProcessor()
    pkt = TelemetryPacket(
        packet_id="PKT-P",
        timestamp=datetime.now(),
        source="gs1",
        milestone="pressurization",
        data={"progress": 42, "status": "in_progress"},
    )
    proc.process_packet(pkt)
    status = proc.milestone_states["pressurization"]
    assert status.progress_percent == 42.0
