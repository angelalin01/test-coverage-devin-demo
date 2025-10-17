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
    
    def test_receive_invalid_packet_increments_error_count(self, receiver):
        """Test that invalid packets increment error count."""
        packet = TelemetryPacket(
            packet_id="",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"status": "in_progress"}
        )
        
        result = receiver.receive_packet(packet)
        assert result is False
        assert receiver.error_count == 1
        assert receiver.packet_count == 0
    
    def test_buffer_overflow_evicts_oldest(self, receiver):
        """Test buffer overflow causes FIFO eviction."""
        for i in range(12):
            packet = TelemetryPacket(
                packet_id=f"PKT-{i:03d}",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"status": "in_progress"}
            )
            receiver.receive_packet(packet)
        
        assert len(receiver.packet_buffer) == 10
        assert receiver.packet_buffer[0].packet_id == "PKT-002"
        assert receiver.packet_buffer[-1].packet_id == "PKT-011"
    
    def test_sequence_number_tracking(self, receiver):
        """Test sequence number tracking updates correctly."""
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"status": "in_progress"},
            sequence_number=42
        )
        
        receiver.receive_packet(packet)
        assert receiver.last_sequence == 42
    
    def test_get_stats(self, receiver):
        """Test get_stats returns all expected fields."""
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"status": "in_progress"}
        )
        receiver.receive_packet(packet)
        
        stats = receiver.get_stats()
        assert stats['packet_count'] == 1
        assert stats['error_count'] == 0
        assert stats['buffer_size'] == 1
        assert stats['buffer_capacity'] == 10


class TestTelemetryReceiverAsync:
    """Test cases for async receiver behavior and silent failures."""
    
    @pytest.fixture
    def receiver(self):
        """Create a telemetry receiver instance."""
        return TelemetryReceiver(buffer_size=10)
    
    @pytest.mark.asyncio
    async def test_async_retries_up_to_three(self, receiver):
        """Test async receiver 'retries up to 3' means 3 retry attempts (4 total) - currently only 2 retries."""
        call_count = []
        
        def failing_receive(packet):
            call_count.append(1)
            return False
        
        receiver.receive_packet = failing_receive
        
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"status": "in_progress"}
        )
        
        result = await receiver.receive_packet_async(packet)
        
        assert len(call_count) == 4, f"Expected 4 attempts (1 initial + 3 retries), got {len(call_count)}"
    
    @pytest.mark.asyncio
    async def test_async_exception_emits_error_event(self, receiver):
        """Test async receiver emits error event on exception instead of swallowing silently."""
        def raising_receive(packet):
            raise ValueError("Simulated error")
        
        receiver.receive_packet = raising_receive
        
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"status": "in_progress"}
        )
        
        result = await receiver.receive_packet_async(packet)
        
        assert result is False
        assert receiver.error_count > 0, "Expected error_count to be incremented when exception occurs"
    
    def test_reorder_preserves_unsequenced_packets(self, receiver):
        """Test _reorder_packets preserves packets without sequence_number."""
        from ingestion.receiver import _reorder_packets
        
        packets = [
            TelemetryPacket(
                packet_id="PKT-001",
                timestamp=datetime.now(),
                source="gs1",
                milestone="engine_chill",
                data={},
                sequence_number=3
            ),
            TelemetryPacket(
                packet_id="PKT-002",
                timestamp=datetime.now(),
                source="gs1",
                milestone="fuel_load",
                data={},
                sequence_number=None
            ),
            TelemetryPacket(
                packet_id="PKT-003",
                timestamp=datetime.now(),
                source="gs1",
                milestone="pressurization",
                data={},
                sequence_number=1
            ),
        ]
        
        reordered = _reorder_packets(packets)
        
        assert len(reordered) == 3, f"Expected 3 packets, got {len(reordered)}"
        assert reordered[0].packet_id == "PKT-003"  # seq 1
        assert reordered[1].packet_id == "PKT-001"  # seq 3
        assert reordered[2].packet_id == "PKT-002"  # no seq - preserved at end
    
    def test_validate_sequence_gap_within_threshold(self, receiver):
        """Test _validate_sequence_gap returns True when gap is within threshold."""
        from ingestion.receiver import _validate_sequence_gap
        
        assert _validate_sequence_gap(current_seq=5, last_seq=2, max_gap=3) is True
        
        assert _validate_sequence_gap(current_seq=5, last_seq=3, max_gap=3) is True
    
    def test_validate_sequence_gap_exceeds_threshold(self, receiver):
        """Test _validate_sequence_gap returns False and increments error_count when gap exceeds threshold."""
        from ingestion.receiver import _validate_sequence_gap
        
        assert _validate_sequence_gap(current_seq=10, last_seq=5, max_gap=3) is False
