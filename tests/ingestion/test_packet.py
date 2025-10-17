import pytest
from datetime import datetime

from ingestion.packet import TelemetryPacket, validate_packet


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
    
    def test_invalid_milestone_raises_error(self):
        """Test that invalid milestone raises ValueError."""
        with pytest.raises(ValueError, match="Invalid milestone"):
            TelemetryPacket(
                packet_id="PKT-002",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="invalid_milestone",
                data={"status": "test"}
            )
    
    def test_validate_packet_missing_data(self):
        """Test validate_packet returns False for empty data."""
        packet = TelemetryPacket(
            packet_id="PKT-003",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={}
        )
        assert validate_packet(packet) is False
