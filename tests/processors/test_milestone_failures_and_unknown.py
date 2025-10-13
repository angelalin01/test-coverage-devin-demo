from datetime import datetime
import pytest
from processors.milestone_processor import MilestoneProcessor, MilestoneState
from ingestion.packet import TelemetryPacket
from pydantic import ValidationError

def test_unknown_milestone_rejected_by_model_validation():
    p = MilestoneProcessor()
    with pytest.raises(ValidationError):
        TelemetryPacket(
            packet_id="UKN-1",
            timestamp=datetime.utcnow(),
            source="gs",
            milestone="nonexistent",
            data={"status": "complete"}
        )

def test_failed_state_sets_error_message():
    p = MilestoneProcessor()
    pkt = TelemetryPacket(
        packet_id="FL-1",
        timestamp=datetime.utcnow(),
        source="gs",
        milestone="engine_chill",
        data={"status": "failed", "error": "sensor fault"}
    )
    assert p.process_packet(pkt) is True
    status = p.get_all_statuses()["engine_chill"]
    assert status.state == MilestoneState.FAILED
    assert status.error_message == "sensor fault"
