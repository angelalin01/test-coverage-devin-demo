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
    
    async def test_receive_packet_async_retries_up_to_3_times(self, receiver):
        """Test that async receiver retries up to 3 times on failure (4 total attempts)."""
        from unittest.mock import Mock, patch
        
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="test_source",
            milestone="engine_chill",
            data={"status": "in_progress"}
        )
        
        call_count = 0
        def mock_receive_packet(p):
            nonlocal call_count
            call_count += 1
            return False
        
        with patch.object(receiver, 'receive_packet', side_effect=mock_receive_packet):
            result = await receiver.receive_packet_async(packet)
        
        assert result is False
        assert call_count == 4
    
    async def test_receive_packet_async_exception_increments_error_count(self, receiver):
        """Test that async exceptions increment error_count instead of silent failure."""
        from unittest.mock import patch
        
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="test_source",
            milestone="engine_chill",
            data={"status": "in_progress"}
        )
        
        initial_error_count = receiver.error_count
        
        with patch.object(receiver, 'receive_packet', side_effect=ValueError("Test error")):
            result = await receiver.receive_packet_async(packet)
        
        assert result is False
        assert receiver.error_count > initial_error_count
    
    def test_reorder_packets_preserves_unsequenced_packets(self):
        """Test that packets without sequence_number are preserved, not dropped."""
        from ingestion.receiver import _reorder_packets
        
        packets = [
            TelemetryPacket(
                packet_id="PKT-003",
                timestamp=datetime.now(),
                source="test",
                milestone="engine_chill",
                data={},
                sequence_number=3
            ),
            TelemetryPacket(
                packet_id="PKT-UNSEQ-1",
                timestamp=datetime.now(),
                source="test",
                milestone="fuel_load",
                data={},
                sequence_number=None
            ),
            TelemetryPacket(
                packet_id="PKT-001",
                timestamp=datetime.now(),
                source="test",
                milestone="pressurization",
                data={},
                sequence_number=1
            ),
            TelemetryPacket(
                packet_id="PKT-UNSEQ-2",
                timestamp=datetime.now(),
                source="test",
                milestone="ignition",
                data={},
                sequence_number=None
            ),
            TelemetryPacket(
                packet_id="PKT-002",
                timestamp=datetime.now(),
                source="test",
                milestone="liftoff",
                data={},
                sequence_number=2
            ),
        ]
        
        reordered = _reorder_packets(packets)
        
        assert len(reordered) == 5
        assert reordered[0].packet_id == "PKT-001"
        assert reordered[1].packet_id == "PKT-002"
        assert reordered[2].packet_id == "PKT-003"
        assert "UNSEQ" in reordered[3].packet_id
        assert "UNSEQ" in reordered[4].packet_id
