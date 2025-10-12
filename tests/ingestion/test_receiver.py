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
    
    @pytest.mark.asyncio
    async def test_receive_packet_async_success(self, receiver):
        """Test async packet reception with immediate success."""
        packet = TelemetryPacket(
            packet_id="PKT-002",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="fuel_load",
            data={"status": "in_progress"}
        )
        
        result = await receiver.receive_packet_async(packet)
        
        assert result is True
        assert receiver.packet_count == 1
        assert len(receiver.packet_buffer) == 1
    
    @pytest.mark.asyncio
    async def test_receive_packet_async_with_retry(self, receiver):
        """Test async packet reception with transient failure and retry."""
        from unittest.mock import patch
        
        packet = TelemetryPacket(
            packet_id="PKT-003",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="pressurization",
            data={"status": "complete"}
        )
        
        call_count = 0
        original_receive = receiver.receive_packet
        
        def mock_receive(pkt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                receiver.error_count += 1
                return False
            return original_receive(pkt)
        
        receiver.receive_packet = mock_receive
        
        result = await receiver.receive_packet_async(packet, retry_count=0)
        
        assert result is True
        assert call_count == 2
        assert receiver.packet_count == 1
        assert receiver.error_count == 1
    
    @pytest.mark.asyncio
    async def test_receive_packet_async_max_retries(self, receiver):
        """Test async packet reception exhausting all retries."""
        from unittest.mock import patch
        
        packet = TelemetryPacket(
            packet_id="PKT-004",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="terminal_count",
            data={"status": "failed"}
        )
        
        with patch.object(receiver, 'receive_packet', return_value=False):
            result = await receiver.receive_packet_async(packet, retry_count=0)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_receive_packet_async_exception_handling(self, receiver):
        """Test async packet reception with exception returns False."""
        from unittest.mock import patch
        
        packet = TelemetryPacket(
            packet_id="PKT-005",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="ignition",
            data={"status": "in_progress"}
        )
        
        with patch.object(receiver, 'receive_packet', side_effect=RuntimeError("Simulated error")):
            result = await receiver.receive_packet_async(packet)
        
        assert result is False
    
    def test_buffer_overflow_eviction(self, receiver):
        """Test that buffer evicts oldest packet when full."""
        for i in range(12):
            packet = TelemetryPacket(
                packet_id=f"PKT-{i:03d}",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"sequence": i}
            )
            receiver.receive_packet(packet)
        
        assert len(receiver.packet_buffer) == 10
        assert receiver.packet_count == 12
    
    def test_get_stats(self, receiver):
        """Test get_stats returns all expected fields."""
        packet = TelemetryPacket(
            packet_id="PKT-100",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="liftoff",
            data={"status": "complete"}
        )
        receiver.receive_packet(packet)
        
        stats = receiver.get_stats()
        
        assert 'packet_count' in stats
        assert 'error_count' in stats
        assert 'buffer_size' in stats
        assert 'buffer_capacity' in stats
        assert stats['packet_count'] == 1
        assert stats['error_count'] == 0
        assert stats['buffer_size'] == 1
        assert stats['buffer_capacity'] == 10
