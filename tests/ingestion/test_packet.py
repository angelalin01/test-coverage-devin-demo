import pytest
from datetime import datetime
from pydantic import ValidationError

from ingestion.packet import TelemetryPacket, PacketValidator


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
        """Test that invalid milestone raises validation error."""
        with pytest.raises(ValidationError):
            TelemetryPacket(
                packet_id="PKT-003",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="invalid_milestone",
                data={}
            )
    
    def test_get_metric_value(self):
        """Test extracting metric values from packet data."""
        packet = TelemetryPacket(
            packet_id="PKT-005",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"temperature": -180.5, "pressure": 100.0}
        )
        
        assert packet.get_metric_value("temperature") == -180.5
        assert packet.get_metric_value("pressure") == 100.0
        assert packet.get_metric_value("nonexistent") is None


class TestPacketValidator:
    """Test cases for PacketValidator class."""
    
    def test_validate_valid_packet(self):
        """Test validation of a valid packet."""
        packet = TelemetryPacket(
            packet_id="PKT-006",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="fuel_load",
            data={"flow_rate": 100.0}
        )
        
        validator = PacketValidator()
        assert validator.validate_packet(packet) is True
    
    def test_validate_packet_without_data(self):
        """Test validation fails for packet without data."""
        packet = TelemetryPacket(
            packet_id="PKT-007",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="fuel_load",
            data={}
        )
        
        validator = PacketValidator()
        assert validator.validate_packet(packet) is False
