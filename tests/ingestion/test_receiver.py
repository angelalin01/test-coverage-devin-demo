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
    
    def test_receive_invalid_packet(self, receiver):
        """Test receiving an invalid packet (empty packet_id)."""
        packet = TelemetryPacket(
            packet_id="",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"temperature": -180.5}
        )
        
        result = receiver.receive_packet(packet)
        assert result is False
        assert receiver.error_count == 1
        assert receiver.packet_count == 0
        assert len(receiver.packet_buffer) == 0
    
    def test_buffer_overflow(self, receiver):
        """Test buffer overflow behavior with FIFO eviction."""
        for i in range(15):
            packet = TelemetryPacket(
                packet_id=f"PKT-{i:03d}",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"temperature": -180.5}
            )
            receiver.receive_packet(packet)
        
        assert len(receiver.packet_buffer) == 10
        assert receiver.packet_count == 15
        assert receiver.packet_buffer[0].packet_id == "PKT-005"
    
    def test_get_stats(self, receiver):
        """Test get_stats returns all expected fields."""
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
    
    @pytest.mark.asyncio
    async def test_receive_packet_async_success(self, receiver):
        """Test async packet reception succeeds."""
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"temperature": -180.5}
        )
        
        result = await receiver.receive_packet_async(packet)
        assert result is True
        assert receiver.packet_count == 1
    
    @pytest.mark.asyncio
    async def test_receive_packet_async_retry_logic(self, receiver):
        """Test async retry attempts up to 3 times as documented."""
        invalid_packet = TelemetryPacket(
            packet_id="",  # Empty packet_id fails validation
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"temperature": -180.5}
        )
        
        result = await receiver.receive_packet_async(invalid_packet)
        assert result is False
        assert receiver.error_count == 3
    
    @pytest.mark.asyncio
    async def test_receive_packet_async_exception_handling(self, receiver):
        """Test async exception handling emits error events."""
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"temperature": -180.5}
        )
        
        receiver.packet_buffer = None  # This will cause an exception
        
        result = await receiver.receive_packet_async(packet)
        assert result is False
        assert receiver.error_count > 0
