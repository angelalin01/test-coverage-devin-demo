from datetime import datetime, timezone
from api.server import StatusAPI, PacketSubmission

def test_status_api_get_readiness_default_no_packets():
    api = StatusAPI()
    readiness = api.get_readiness()
    assert readiness.level.value in {"not_ready", "partial", "ready", "scrubbed"}
    assert readiness.overall_progress >= 0.0

def test_status_api_submit_packet_and_readiness_progress():
    api = StatusAPI()
    packet = PacketSubmission(
        packet_id="PKT-API-001",
        timestamp=datetime.now(timezone.utc),
        source="ground_station_1",
        milestone="engine_chill",
        data={"status": "in_progress"}
    )
    resp = api.submit_packet(packet)
    assert resp["status"] == "accepted"
    assert resp["packet_id"] == "PKT-API-001"
    readiness = api.get_readiness()
    assert "engine_chill" in readiness.pending_milestones or "engine_chill" in readiness.ready_milestones
