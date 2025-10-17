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
    
    def test_buffer_overflow_eviction(self, receiver):
        """Test that buffer overflow evicts oldest packet."""
        for i in range(12):
            packet = TelemetryPacket(
                packet_id=f"PKT-{i:03d}",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"index": i}
            )
            receiver.receive_packet(packet)
        
        assert len(receiver.packet_buffer) == 10
        assert receiver.packet_count == 12
        assert receiver.packet_buffer[0].data["index"] == 2
    
    def test_get_stats(self, receiver):
        """Test get_stats returns correct statistics."""
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"temperature": -180.5}
        )
        receiver.receive_packet(packet)
        
        stats = receiver.get_stats()
        assert stats['packet_count'] == 1
        assert stats['error_count'] == 0
        assert stats['buffer_size'] == 1
        assert stats['buffer_capacity'] == 10
    
    def test_sequence_number_tracking(self, receiver):
        """Test that sequence numbers are tracked correctly."""
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"temperature": -180.5},
            sequence_number=42
        )
        receiver.receive_packet(packet)
        
        assert receiver.last_sequence == 42
    
    def test_invalid_packet_increments_error_count(self, receiver):
        """Test that invalid packets increment error count."""
        packet = TelemetryPacket(
            packet_id="",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={}
        )
        
        result = receiver.receive_packet(packet)
        assert result is False
        assert receiver.error_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_attempts_up_to_3_times(self, receiver):
        """Test that async receiver retries up to 3 times on transient failures."""
        from unittest.mock import patch
        
        attempt_count = 0
        
        def mock_receive_packet(packet):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                return False
            return True
        
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"temperature": -180.5}
        )
        
        with patch.object(receiver, 'receive_packet', side_effect=mock_receive_packet):
            result = await receiver.receive_packet_async(packet)
            assert result is True
            assert attempt_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_stops_after_max_attempts(self, receiver):
        """Test that retry stops after maximum attempts (initial + 3 retries = 4 total)."""
        from unittest.mock import patch
        
        attempt_count = 0
        
        def mock_receive_packet(packet):
            nonlocal attempt_count
            attempt_count += 1
            return False
        
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"temperature": -180.5}
        )
        
        with patch.object(receiver, 'receive_packet', side_effect=mock_receive_packet):
            result = await receiver.receive_packet_async(packet)
            assert result is False
            assert attempt_count == 4
    
    @pytest.mark.asyncio
    async def test_async_exception_increments_error_count(self, receiver):
        """Test that async exceptions increment error count and don't silently fail."""
        from unittest.mock import patch
        
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"temperature": -180.5}
        )
        
        with patch.object(receiver, 'receive_packet', side_effect=RuntimeError("Network error")):
            result = await receiver.receive_packet_async(packet)
            assert result is False
            assert receiver.error_count == 1
    
    def test_sequence_gap_validation(self, receiver):
        """Test that sequence gaps > 3 are detected and rejected."""
        from ingestion.receiver import _validate_sequence_gap
        
        assert _validate_sequence_gap(5, 1, max_gap=3) is False
        assert _validate_sequence_gap(4, 1, max_gap=3) is True
        assert _validate_sequence_gap(2, 1, max_gap=3) is True
    
    def test_reorder_packets_preserves_unsequenced(self):
        """Test that packets without sequence numbers are preserved during reordering."""
        from ingestion.receiver import _reorder_packets
        
        packets = [
            TelemetryPacket(
                packet_id="PKT-003",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"temperature": -180.5},
                sequence_number=3
            ),
            TelemetryPacket(
                packet_id="PKT-001",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="fuel_load",
                data={"pressure": 100.0}
            ),
            TelemetryPacket(
                packet_id="PKT-002",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="pressurization",
                data={"status": "complete"},
                sequence_number=1
            ),
        ]
        
        reordered = _reorder_packets(packets)
        
        assert len(reordered) == 3
        assert reordered[0].packet_id == "PKT-002"
        assert reordered[1].packet_id == "PKT-003"
        packet_ids = [p.packet_id for p in reordered]
        assert "PKT-001" in packet_ids
