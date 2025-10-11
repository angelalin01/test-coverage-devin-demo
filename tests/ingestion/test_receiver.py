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
        """Test receiving an invalid packet increases error count."""
        packet = TelemetryPacket(
            packet_id="PKT-002",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="fuel_load",
            data={}
        )
        
        result = receiver.receive_packet(packet)
        assert result is False
        assert receiver.error_count == 1
        assert len(receiver.packet_buffer) == 0
    
    def test_buffer_overflow(self, receiver):
        """Test that buffer size is respected."""
        for i in range(15):
            packet = TelemetryPacket(
                packet_id=f"PKT-{i:03d}",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"value": i}
            )
            receiver.receive_packet(packet)
        
        assert len(receiver.packet_buffer) == 10
        assert receiver.packet_count == 15
    
    def test_get_packets_all(self, receiver):
        """Test retrieving all packets."""
        packets = [
            TelemetryPacket(
                packet_id=f"PKT-{i}",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"value": i}
            )
            for i in range(5)
        ]
        
        for packet in packets:
            receiver.receive_packet(packet)
        
        retrieved = receiver.get_packets()
        assert len(retrieved) == 5
    
    def test_get_packets_filtered_by_milestone(self, receiver):
        """Test retrieving packets filtered by milestone."""
        milestones = ["engine_chill", "fuel_load", "engine_chill"]
        
        for i, milestone in enumerate(milestones):
            packet = TelemetryPacket(
                packet_id=f"PKT-{i}",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone=milestone,
                data={"value": i}
            )
            receiver.receive_packet(packet)
        
        chill_packets = receiver.get_packets(milestone="engine_chill")
        assert len(chill_packets) == 2
    
    def test_get_latest_packet(self, receiver):
        """Test getting the latest packet."""
        import time
        
        for i in range(3):
            packet = TelemetryPacket(
                packet_id=f"PKT-{i}",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="engine_chill",
                data={"value": i}
            )
            receiver.receive_packet(packet)
            time.sleep(0.01)
        
        latest = receiver.get_latest_packet()
        assert latest is not None
        assert latest.data["value"] == 2
    
    def test_clear_buffer(self, receiver):
        """Test clearing the buffer."""
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"temperature": -180.5}
        )
        receiver.receive_packet(packet)
        
        assert len(receiver.packet_buffer) == 1
        receiver.clear_buffer()
        assert len(receiver.packet_buffer) == 0
    
    def test_get_stats(self, receiver):
        """Test retrieving receiver statistics."""
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
    async def test_receive_packet_async(self, receiver):
        """Test async packet reception."""
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
