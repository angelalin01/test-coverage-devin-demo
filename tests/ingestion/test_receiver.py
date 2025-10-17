import pytest
from datetime import datetime

from ingestion.receiver import TelemetryReceiver
from ingestion.packet import TelemetryPacket


class TestTelemetryReceiver:
    """Test cases for TelemetryReceiver class."""
    
    @pytest.fixture
    def receiver(self):
        """Create a telemetry receiver instance."""
        return TelemetryReceiver(buffer_size=10)
    
    def test_receive_valid_packet(self, receiver):
        """Test receiving a valid packet."""
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"temperature": -180.5}
        )
        
        result = receiver.receive_packet(packet)
        assert result is True
        assert receiver.packet_count == 1
        assert len(receiver.packet_buffer) == 1
    
    def test_buffer_overflow_evicts_oldest(self, receiver):
        """Test that buffer overflow evicts oldest packet."""
        for i in range(12):
            packet = TelemetryPacket(
                packet_id=f"PKT-{i:03d}",
                timestamp=datetime.now(),
                source="test_source",
                milestone="engine_chill",
                data={"index": i}
            )
            receiver.receive_packet(packet)
        
        assert len(receiver.packet_buffer) == 10
        assert receiver.packet_buffer[0].packet_id == "PKT-002"
        assert receiver.packet_buffer[-1].packet_id == "PKT-011"
    
    def test_receive_packet_tracks_sequence_number(self, receiver):
        """Test that sequence numbers are tracked."""
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="test_source",
            milestone="engine_chill",
            data={"status": "in_progress"},
            sequence_number=42
        )
        receiver.receive_packet(packet)
        assert receiver.last_sequence == 42
    
    def test_get_stats_returns_all_fields(self, receiver):
        """Test get_stats returns all expected fields."""
        stats = receiver.get_stats()
        assert "packet_count" in stats
        assert "error_count" in stats
        assert "buffer_size" in stats
        assert "buffer_capacity" in stats
        assert stats["buffer_capacity"] == 10
