from datetime import datetime
from ingestion.receiver import TelemetryReceiver
from ingestion.packet import TelemetryPacket

def test_buffer_eviction_fifo_when_at_capacity():
    r = TelemetryReceiver(buffer_size=2)
    p1 = TelemetryPacket(packet_id="A", timestamp=datetime.utcnow(), source="s", milestone="engine_chill", data={"v":1})
    p2 = TelemetryPacket(packet_id="B", timestamp=datetime.utcnow(), source="s", milestone="fuel_load", data={"v":2})
    p3 = TelemetryPacket(packet_id="C", timestamp=datetime.utcnow(), source="s", milestone="pressurization", data={"v":3})
    assert r.receive_packet(p1) is True
    assert r.receive_packet(p2) is True
    assert len(r.packet_buffer) == 2
    assert r.packet_buffer[0].packet_id == "A"
    assert r.receive_packet(p3) is True
    assert len(r.packet_buffer) == 2
    ids = [p.packet_id for p in r.packet_buffer]
    assert ids == ["B", "C"]
