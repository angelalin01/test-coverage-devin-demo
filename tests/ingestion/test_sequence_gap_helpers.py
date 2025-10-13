from ingestion.receiver import _validate_sequence_gap, _reorder_packets
from ingestion.packet import TelemetryPacket
from datetime import datetime

def test_validate_sequence_gap_cases():
    assert _validate_sequence_gap(5, 5) is False
    assert _validate_sequence_gap(5, 6) is False
    assert _validate_sequence_gap(7, 5) is True
    assert _validate_sequence_gap(8, 5) is True
    assert _validate_sequence_gap(9, 5) is False
    assert _validate_sequence_gap(10, 5) is False

def test_reorder_packets_drops_unsequenced_and_sorts():
    p1 = TelemetryPacket(packet_id="A", timestamp=datetime.utcnow(), source="s", milestone="engine_chill", data={"v":1}, sequence_number=3)
    p2 = TelemetryPacket(packet_id="B", timestamp=datetime.utcnow(), source="s", milestone="fuel_load", data={"v":2}, sequence_number=None)
    p3 = TelemetryPacket(packet_id="C", timestamp=datetime.utcnow(), source="s", milestone="pressurization", data={"v":3}, sequence_number=1)
    ordered = _reorder_packets([p1, p2, p3])
    ids = [p.packet_id for p in ordered]
    assert ids == ["C", "A"]
