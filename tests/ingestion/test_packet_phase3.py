import pytest
from datetime import datetime, timezone

from ingestion.packet import TelemetryPacket, validate_packet


class TestTelemetryPacketPhase3:
    def test_validate_packet_returns_false_for_empty_data(self):
        packet = TelemetryPacket(
            packet_id="EMPTY-1",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="engine_chill",
            data={}
        )
        
        result = validate_packet(packet)
        assert result is False
