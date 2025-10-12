import pytest
from datetime import datetime

from ingestion.packet import TelemetryPacket


class TestTelemetryPacket:
    """Test cases for TelemetryPacket class."""
    
    def test_create_valid_packet(self):
        """Test creating a valid telemetry packet."""
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"temperature": -180.5, "status": "in_progress"}
        )
        
        assert packet.packet_id == "PKT-001"
        assert packet.source == "ground_station_1"
        assert packet.milestone == "engine_chill"
        assert packet.data["temperature"] == -180.5
