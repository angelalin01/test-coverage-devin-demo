import pytest
from datetime import datetime
from unittest.mock import Mock, patch

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
        """Test that oldest packet is evicted when buffer is full."""
        for i in range(11):
            packet = TelemetryPacket(
                packet_id=f"PKT-{i:03d}",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="pressurization",
                data={"sequence": i}
            )
            receiver.receive_packet(packet)
        
        assert len(receiver.packet_buffer) == 10
        assert receiver.packet_buffer[0].packet_id == "PKT-001"
        assert receiver.packet_buffer[-1].packet_id == "PKT-010"
    
    @pytest.mark.asyncio
    async def test_async_retry_with_exponential_backoff(self, receiver):
        """Test async retry uses exponential backoff on failure."""
        invalid_packet = TelemetryPacket(
            packet_id="",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="liftoff",
            data={"test": "data"}
        )
        
        with patch('asyncio.sleep') as mock_sleep:
            result = await receiver.receive_packet_async(invalid_packet)
            
            assert result is False
            assert receiver.error_count == 3
            
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert sleep_calls[1] == 0.5
            assert sleep_calls[3] == 1.0
    
    @pytest.mark.asyncio
    async def test_async_exception_emits_error_event(self, receiver):
        """Test async exceptions emit error events instead of silent failure."""
        packet = TelemetryPacket(
            packet_id="PKT-ERROR",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="ignition",
            data={"test": "data"}
        )
        
        with patch.object(receiver, 'receive_packet', side_effect=RuntimeError("Simulated error")):
            with patch.object(receiver, 'emit_error_event') as mock_emit:
                result = await receiver.receive_packet_async(packet)
                
                assert result is False
                mock_emit.assert_called_once()
                call_args = mock_emit.call_args[1]
                assert 'RuntimeError' in call_args['error_type']
                assert 'Simulated error' in call_args['error_message']
    
    def test_out_of_order_packet_reordering_within_gap(self, receiver):
        """Test packets are reordered when out-of-order within max gap."""
        packets = [
            TelemetryPacket(
                packet_id="PKT-001",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="fuel_load",
                data={"test": "data"},
                sequence_number=1
            ),
            TelemetryPacket(
                packet_id="PKT-003",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="fuel_load",
                data={"test": "data"},
                sequence_number=3
            ),
            TelemetryPacket(
                packet_id="PKT-002",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone="fuel_load",
                data={"test": "data"},
                sequence_number=2
            )
        ]
        
        for packet in packets:
            receiver.receive_packet(packet)
        
        assert len(receiver.packet_buffer) == 3
        assert receiver.packet_buffer[0].sequence_number == 1
        assert receiver.packet_buffer[1].sequence_number == 2
        assert receiver.packet_buffer[2].sequence_number == 3
    
    def test_out_of_order_packet_beyond_gap_rejected(self, receiver):
        """Test packets with gap > 3 are rejected."""
        packet1 = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="pressurization",
            data={"test": "data"},
            sequence_number=1
        )
        packet2 = TelemetryPacket(
            packet_id="PKT-005",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="pressurization",
            data={"test": "data"},
            sequence_number=5
        )
        
        result1 = receiver.receive_packet(packet1)
        assert result1 is True
        
        result2 = receiver.receive_packet(packet2)
        assert result2 is False
        assert receiver.error_count == 1
