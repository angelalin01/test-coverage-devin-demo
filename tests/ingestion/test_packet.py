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
    
    @pytest.mark.parametrize("invalid_milestone", [
        "invalid_stage",
        "launch_complete",
        "pre_flight",
        "",
        "IGNITION"
    ])
    def test_invalid_milestone_raises_error(self, invalid_milestone):
        """Test that invalid milestones raise ValueError."""
        with pytest.raises(ValueError, match="Invalid milestone"):
            TelemetryPacket(
                packet_id="PKT-002",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone=invalid_milestone,
                data={"status": "test"}
            )
    
    def test_validate_packet_with_empty_packet_id(self):
        """Test validate_packet returns False for empty packet_id."""
        packet = TelemetryPacket(
            packet_id="",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="liftoff",
            data={"status": "test"}
        )
        assert validate_packet(packet) is False
    
    def test_validate_packet_with_empty_data(self):
        """Test validate_packet returns False for empty data."""
        packet = TelemetryPacket(
            packet_id="PKT-003",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="fuel_load",
            data={}
        )
        assert validate_packet(packet) is False
