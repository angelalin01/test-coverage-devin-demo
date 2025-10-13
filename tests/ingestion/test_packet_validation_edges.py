from datetime import datetime
from ingestion.receiver import TelemetryReceiver
from ingestion.packet import TelemetryPacket

def test_receive_invalid_packet_empty_packet_id_increments_error():
    r = TelemetryReceiver(buffer_size=3)
    pkt = TelemetryPacket(
        packet_id="",
        timestamp=datetime.utcnow(),
        source="gs",
        milestone="engine_chill",
        data={"x": 1.0}
    )
    result = r.receive_packet(pkt)
    assert result is False
    assert r.error_count == 1
    assert r.packet_count == 0
    assert len(r.packet_buffer) == 0
