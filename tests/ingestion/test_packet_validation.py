import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from ingestion.packet import TelemetryPacket, validate_packet


class TestTelemetryPacketValidation:
    def test_invalid_milestone_raises(self):
        with pytest.raises((ValueError, ValidationError)):
            TelemetryPacket(
                packet_id="PKT-INVALID",
                timestamp=datetime.now(),
                source="gs1",
                milestone="not_a_real_milestone",
                data={"status": "in_progress"},
            )

    def test_empty_data_is_invalid_for_validate_packet(self):
        pkt = TelemetryPacket(
            packet_id="PKT-EMPTY",
            timestamp=datetime.now(),
            source="gs1",
            milestone="engine_chill",
            data={},
        )
        assert validate_packet(pkt) is False
