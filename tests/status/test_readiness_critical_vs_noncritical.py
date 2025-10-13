from datetime import datetime
from processors.milestone_processor import MilestoneProcessor
from ingestion.packet import TelemetryPacket
from status.readiness import ReadinessComputer, ReadinessLevel

def test_critical_failure_scrubs_launch():
    proc = MilestoneProcessor()
    rc = ReadinessComputer(proc)
    pkt = TelemetryPacket(
        packet_id="CRIT-F",
        timestamp=datetime.utcnow(),
        source="gs",
        milestone="engine_chill",
        data={"status": "failed", "error": "pump"}
    )
    assert proc.process_packet(pkt) is True
    readiness = rc.compute_readiness()
    assert readiness.level == ReadinessLevel.SCRUBBED
    assert "engine_chill" in readiness.failed_milestones

def test_critical_ready_but_pending_others_is_partial():
    proc = MilestoneProcessor()
    rc = ReadinessComputer(proc)
    for m in ["engine_chill", "fuel_load", "pressurization"]:
        pkt = TelemetryPacket(
            packet_id=f"PKT-{m}",
            timestamp=datetime.utcnow(),
            source="gs",
            milestone=m,
            data={"status": "complete"}
        )
        assert proc.process_packet(pkt) is True
    readiness = rc.compute_readiness()
    assert readiness.level == ReadinessLevel.PARTIAL
    assert len(readiness.pending_milestones) > 0
