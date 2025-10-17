import pytest
from datetime import datetime

from ingestion.receiver import TelemetryReceiver, _validate_sequence_gap, _reorder_packets
from ingestion.packet import TelemetryPacket


class TestSequenceValidation:
    """Test cases for sequence validation and reordering."""
    
    def test_validate_sequence_gap_valid(self):
        """Test sequence gap validation within threshold."""
        assert _validate_sequence_gap(5, 2, max_gap=3) is True
        assert _validate_sequence_gap(5, 4, max_gap=3) is True
    
    def test_validate_sequence_gap_exceeded(self):
        """Test sequence gap validation when gap exceeds threshold."""
        assert _validate_sequence_gap(10, 2, max_gap=3) is False
    
    def test_validate_sequence_gap_non_sequential(self):
        """Test sequence gap validation for non-sequential packets."""
        assert _validate_sequence_gap(2, 5, max_gap=3) is False
        assert _validate_sequence_gap(5, 5, max_gap=3) is False
    
    def test_reorder_packets_by_sequence(self):
        """Test packet reordering by sequence number."""
        packets = [
            TelemetryPacket(
                packet_id="PKT-003",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"temp": 1},
                sequence_number=3
            ),
            TelemetryPacket(
                packet_id="PKT-001",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"temp": 2},
                sequence_number=1
            ),
            TelemetryPacket(
                packet_id="PKT-002",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"temp": 3},
                sequence_number=2
            ),
        ]
        
        reordered = _reorder_packets(packets)
        assert len(reordered) == 3
        assert reordered[0].packet_id == "PKT-001"
        assert reordered[1].packet_id == "PKT-002"
        assert reordered[2].packet_id == "PKT-003"
    
    def test_reorder_packets_preserves_unsequenced(self):
        """Test that reordering handles packets without sequence numbers."""
        packets = [
            TelemetryPacket(
                packet_id="PKT-002",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"temp": 1},
                sequence_number=2
            ),
            TelemetryPacket(
                packet_id="PKT-NO-SEQ",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"temp": 2}
            ),
            TelemetryPacket(
                packet_id="PKT-001",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"temp": 3},
                sequence_number=1
            ),
        ]
        
        reordered = _reorder_packets(packets)
        assert len(reordered) == 2
        assert reordered[0].packet_id == "PKT-001"
        assert reordered[1].packet_id == "PKT-002"


class TestSequenceTracking:
    """Test sequence number tracking in receiver."""
    
    @pytest.fixture
    def receiver(self):
        """Create a telemetry receiver instance."""
        return TelemetryReceiver(buffer_size=10)
    
    def test_sequence_number_tracking(self, receiver):
        """Test that receiver tracks last sequence number."""
        packet1 = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"temperature": -180.5},
            sequence_number=1
        )
        
        packet2 = TelemetryPacket(
            packet_id="PKT-002",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"temperature": -180.5},
            sequence_number=2
        )
        
        receiver.receive_packet(packet1)
        assert receiver.last_sequence == 1
        
        receiver.receive_packet(packet2)
        assert receiver.last_sequence == 2
