from datetime import datetime
from ingestion.receiver import TelemetryReceiver
from ingestion.packet import TelemetryPacket

def test_get_stats_after_receive():
    r = TelemetryReceiver(buffer_size=5)
    pkt = TelemetryPacket(
        packet_id="PKT-STAT-1",
        timestamp=datetime.utcnow(),
        source="gs",
        milestone="engine_chill",
        data={"temperature": -150.0}
    )
    assert r.receive_packet(pkt) is True
    stats = r.get_stats()
    assert stats["packet_count"] == 1
    assert stats["error_count"] == 0
    assert stats["buffer_size"] == 1
    assert stats["buffer_capacity"] == 5
