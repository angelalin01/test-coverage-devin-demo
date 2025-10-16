import pytest
from datetime import datetime

from ingestion.receiver import TelemetryReceiver
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
