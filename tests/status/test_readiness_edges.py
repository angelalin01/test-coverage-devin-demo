from datetime import datetime

from status.readiness import ReadinessComputer, ReadinessLevel
from processors.milestone_processor import MilestoneProcessor
from ingestion.packet import TelemetryPacket


def test_readiness_scrubbed_when_critical_failed():
    proc = MilestoneProcessor()
    pkt = TelemetryPacket(
        packet_id="PKT-F1",
        timestamp=datetime.now(),
        source="gs1",
        milestone="engine_chill",  # critical
        data={"status": "failed", "error": "leak"},
    )
    proc.process_packet(pkt)
    readiness = ReadinessComputer(proc).compute_readiness()
    assert readiness.level == ReadinessLevel.SCRUBBED
    assert "scrubbed" in readiness.message.lower()


def test_readiness_partial_when_critical_ready_but_pending_remain():
    proc = MilestoneProcessor()
    for m in ["engine_chill", "fuel_load", "pressurization"]:
        pkt = TelemetryPacket(
            packet_id=f"PKT-{m}",
            timestamp=datetime.now(),
            source="gs1",
            milestone=m,
            data={"status": "complete"},
        )
        proc.process_packet(pkt)
    readiness = ReadinessComputer(proc).compute_readiness()
    assert readiness.level == ReadinessLevel.PARTIAL
    assert "pending" in readiness.message.lower()
