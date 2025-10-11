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
    
    def test_packet_with_sequence_number(self):
        """Test packet with sequence number."""
        packet = TelemetryPacket(
            packet_id="PKT-002",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="fuel_load",
            data={"flow_rate": 100.0},
            sequence_number=42
        )
        
        assert packet.sequence_number == 42
    
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
    
    def test_is_valid_returns_true_for_complete_packet(self):
        """Test is_valid returns True for complete packet."""
        packet = TelemetryPacket(
            packet_id="PKT-004",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="pressurization",
            data={"pressure": 150.0}
        )
        
        assert packet.is_valid() is True
    
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
    
    def test_validate_sequence_in_order(self):
        """Test sequence validation for ordered packets."""
        packets = [
            TelemetryPacket(
                packet_id=f"PKT-{i}",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"value": i},
                sequence_number=i
            )
            for i in range(1, 4)
        ]
        
        validator = PacketValidator()
        assert validator.validate_sequence(packets) is True
    
    def test_validate_sequence_out_of_order(self):
        """Test sequence validation detects out-of-order packets."""
        packets = [
            TelemetryPacket(
                packet_id="PKT-1",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"value": 1},
                sequence_number=1
            ),
            TelemetryPacket(
                packet_id="PKT-3",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"value": 3},
                sequence_number=3
            ),
            TelemetryPacket(
                packet_id="PKT-2",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"value": 2},
                sequence_number=2
            )
        ]
        
        validator = PacketValidator()
        assert validator.validate_sequence(packets) is False
    
    def test_detect_duplicates(self):
        """Test duplicate detection."""
        packets = [
            TelemetryPacket(
                packet_id="PKT-001",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"value": 1}
            ),
            TelemetryPacket(
                packet_id="PKT-002",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"value": 2}
            ),
            TelemetryPacket(
                packet_id="PKT-001",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"value": 3}
            )
        ]
        
        validator = PacketValidator()
        duplicates = validator.detect_duplicates(packets)
        assert len(duplicates) == 1
        assert "PKT-001" in duplicates
