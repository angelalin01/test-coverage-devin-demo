import pytest
import asyncio
from datetime import datetime

from ingestion.receiver import TelemetryReceiver
from ingestion.packet import TelemetryPacket
from tests.test_utils import create_test_packet


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
    
    @pytest.mark.asyncio
    async def test_receive_packet_async_success(self, receiver):
        """Test async packet reception basic success path."""
        packet = create_test_packet(
            packet_id="PKT-ASYNC-001",
            milestone="fuel_load",
            data={"status": "in_progress"}
        )
        
        result = await receiver.receive_packet_async(packet)
        assert result is True
        assert receiver.packet_count == 1
        assert len(receiver.packet_buffer) == 1
    
    def test_get_stats(self, receiver):
        """Test get_stats returns proper statistics."""
        packet1 = create_test_packet(packet_id="PKT-001")
        packet2 = create_test_packet(packet_id="PKT-002")
        
        receiver.receive_packet(packet1)
        receiver.receive_packet(packet2)
        
        stats = receiver.get_stats()
        assert stats['packet_count'] == 2
        assert stats['error_count'] == 0
        assert stats['buffer_size'] == 2
        assert stats['buffer_capacity'] == 10
