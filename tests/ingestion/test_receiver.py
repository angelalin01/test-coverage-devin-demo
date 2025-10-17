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
    
    @pytest.mark.asyncio
    async def test_async_retry_attempts_three_times(self, receiver):
        """Test async receiver retries up to 3 times (currently only retries 2 times - BUG)."""
        invalid_packet = TelemetryPacket(
            packet_id="",
            timestamp=datetime.now(),
            source="test",
            milestone="engine_chill",
            data={}
        )
        
        result = await receiver.receive_packet_async(invalid_packet, retry_count=0)
        assert result is False
        assert receiver.error_count == 4
    
    @pytest.mark.asyncio
    async def test_async_exception_increments_error_count(self, receiver):
        """Test async exceptions increment error_count instead of silent failure."""
        class BrokenPacket(TelemetryPacket):
            def __init__(self):
                pass
        
        broken = BrokenPacket()
        result = await receiver.receive_packet_async(broken, retry_count=0)
        assert result is False
        assert receiver.error_count > 0
    
    def test_reorder_packets_preserves_unsequenced(self, receiver):
        """Test packet reordering preserves packets without sequence numbers."""
        from ingestion.receiver import _reorder_packets
        
        packet1 = create_test_packet(packet_id="PKT-001", sequence_number=2)
        packet2 = create_test_packet(packet_id="PKT-002", sequence_number=None)
        packet3 = create_test_packet(packet_id="PKT-003", sequence_number=1)
        
        buffer = [packet1, packet2, packet3]
        reordered = _reorder_packets(buffer)
        
        assert len(reordered) == 3
        assert reordered[0].packet_id == "PKT-003"
        assert reordered[1].packet_id == "PKT-001"
        assert reordered[2].packet_id == "PKT-002"
