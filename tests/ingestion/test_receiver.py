import pytest
from datetime import datetime

from ingestion.receiver import TelemetryReceiver, _validate_sequence_gap, _reorder_packets
from ingestion.packet import TelemetryPacket


@pytest.mark.asyncio
async def test_receive_packet_async_success():
    """Test async packet reception with valid packet."""
    receiver = TelemetryReceiver(buffer_size=10)
    packet = TelemetryPacket(
        packet_id="PKT-ASYNC-001",
        timestamp=datetime.now(),
        source="ground_station_1",
        milestone="engine_chill",
        data={"temperature": -180.5}
    )
    
    result = await receiver.receive_packet_async(packet)
    assert result is True
    assert receiver.packet_count == 1


@pytest.mark.asyncio
async def test_receive_packet_async_retry_attempts():
    """Test async retry logic attempts 3 times total for invalid packets."""
    receiver = TelemetryReceiver(buffer_size=10)
    
    packet = TelemetryPacket(
        packet_id="PKT-ASYNC-002",
        timestamp=datetime.now(),
        source="ground_station_1",
        milestone="engine_chill",
        data={}
    )
    
    result = await receiver.receive_packet_async(packet)
    assert result is False
    assert receiver.error_count == 3


@pytest.mark.asyncio
async def test_receive_packet_async_exception_handling():
    """Test async exception handling returns False without crashing."""
    
    class FailingReceiver(TelemetryReceiver):
        def receive_packet(self, packet):
            raise RuntimeError("Simulated internal error")
    
    receiver = FailingReceiver(buffer_size=10)
    packet = TelemetryPacket(
        packet_id="PKT-ASYNC-003",
        timestamp=datetime.now(),
        source="ground_station_1",
        milestone="engine_chill",
        data={"temp": 100}
    )
    
    result = await receiver.receive_packet_async(packet)
    assert result is False


def test_validate_sequence_gap_within_threshold():
    """Test sequence gap validation accepts gaps <= 3."""
    assert _validate_sequence_gap(current_seq=5, last_seq=2, max_gap=3) is True
    assert _validate_sequence_gap(current_seq=10, last_seq=7, max_gap=3) is True


def test_validate_sequence_gap_exceeds_threshold():
    """Test sequence gap validation rejects gaps > 3."""
    assert _validate_sequence_gap(current_seq=10, last_seq=5, max_gap=3) is False


def test_validate_sequence_gap_backwards():
    """Test sequence gap validation rejects backwards sequences."""
    assert _validate_sequence_gap(current_seq=5, last_seq=10, max_gap=3) is False
    assert _validate_sequence_gap(current_seq=5, last_seq=5, max_gap=3) is False


def test_reorder_packets_with_sequence_numbers():
    """Test packet reordering sorts by sequence number."""
    packets = [
        TelemetryPacket(
            packet_id="PKT-003", timestamp=datetime.now(), source="gs1",
            milestone="engine_chill", data={"x": 3}, sequence_number=3
        ),
        TelemetryPacket(
            packet_id="PKT-001", timestamp=datetime.now(), source="gs1",
            milestone="engine_chill", data={"x": 1}, sequence_number=1
        ),
        TelemetryPacket(
            packet_id="PKT-002", timestamp=datetime.now(), source="gs1",
            milestone="engine_chill", data={"x": 2}, sequence_number=2
        ),
    ]
    
    reordered = _reorder_packets(packets)
    assert len(reordered) == 3
    assert reordered[0].sequence_number == 1
    assert reordered[1].sequence_number == 2
    assert reordered[2].sequence_number == 3


def test_reorder_packets_drops_unsequenced():
    """Test packet reordering drops packets without sequence numbers."""
    packets = [
        TelemetryPacket(
            packet_id="PKT-001", timestamp=datetime.now(), source="gs1",
            milestone="engine_chill", data={"x": 1}, sequence_number=1
        ),
        TelemetryPacket(
            packet_id="PKT-NO-SEQ", timestamp=datetime.now(), source="gs1",
            milestone="engine_chill", data={"x": 0}
        ),
    ]
    
    reordered = _reorder_packets(packets)
    assert len(reordered) == 1
    assert reordered[0].sequence_number == 1


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
    
    def test_receive_invalid_packet(self, receiver):
        """Test receiving an invalid packet increments error count."""
        packet = TelemetryPacket(
            packet_id="PKT-002",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={}
        )
        
        result = receiver.receive_packet(packet)
        assert result is False
        assert receiver.error_count == 1
        assert receiver.packet_count == 0
    
    def test_buffer_eviction_when_full(self, receiver):
        """Test FIFO buffer eviction when exceeding capacity."""
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
        assert receiver.packet_buffer[0].packet_id == "PKT-002"
    
    def test_sequence_number_tracking(self, receiver):
        """Test sequence number is tracked when present."""
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
    
    def test_get_stats(self, receiver):
        """Test statistics reporting."""
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
