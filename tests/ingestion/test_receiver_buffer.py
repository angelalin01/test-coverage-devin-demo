from datetime import datetime

from ingestion.receiver import TelemetryReceiver
from ingestion.packet import TelemetryPacket


class TestTelemetryReceiverBuffering:
    def test_buffer_eviction_when_at_capacity(self):
        r = TelemetryReceiver(buffer_size=1)
        p1 = TelemetryPacket(
            packet_id="P1",
            timestamp=datetime.now(),
            source="gs1",
            milestone="engine_chill",
            data={"status": "in_progress"},
        )
        p2 = TelemetryPacket(
            packet_id="P2",
            timestamp=datetime.now(),
            source="gs1",
            milestone="engine_chill",
            data={"status": "in_progress"},
        )

        assert r.receive_packet(p1) is True
        assert len(r.packet_buffer) == 1
        assert r.packet_buffer[0].packet_id == "P1"

        assert r.receive_packet(p2) is True
        assert len(r.packet_buffer) == 1
        assert r.packet_buffer[0].packet_id == "P2"
        assert r.packet_count == 2
