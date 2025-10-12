import asyncio
from typing import List
from .packet import TelemetryPacket, validate_packet


class TelemetryReceiver:
    """
    Receives and buffers telemetry packets from ground systems.
    """
    
    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self.packet_buffer: List[TelemetryPacket] = []
        self.packet_count = 0
        self.error_count = 0
        self.reorder_buffer: List[TelemetryPacket] = []
        self.max_sequence_gap = 3
        self.last_sequence = None
    
    def receive_packet(self, packet: TelemetryPacket) -> bool:
        """
        Receive and buffer a single telemetry packet.
        
        Args:
            packet: The telemetry packet to receive
            
        Returns:
            True if packet was accepted, False otherwise
        """
        if not validate_packet(packet):
            self.error_count += 1
            return False

        if packet.sequence_number is not None:
            if self.last_sequence is not None:
                if packet.sequence_number <= self.last_sequence or (packet.sequence_number - self.last_sequence) > self.max_sequence_gap:
                    self.error_count += 1
                    return False
            self.last_sequence = packet.sequence_number
        
        if len(self.packet_buffer) >= self.buffer_size:
            self.packet_buffer.pop(0)
        
        self.packet_buffer.append(packet)
        self.packet_count += 1
        
        return True
    
    async def receive_packet_async(self, packet: TelemetryPacket, retry_count: int = 0) -> bool:
        """
        Asynchronously receive and buffer a telemetry packet.
        
        Args:
            packet: The telemetry packet to receive
            retry_count: Current retry attempt number
            
        Returns:
            True if packet was accepted, False otherwise
        """
        try:
            await asyncio.sleep(0)
            result = self.receive_packet(packet)
            if not result:
                if retry_count < 3:
                    backoff = 0.5 * (2 ** retry_count)
                    await asyncio.sleep(backoff)
                    return await self.receive_packet_async(packet, retry_count + 1)
                self.error_count += 1
                return False
            return result
        except Exception:
            self.error_count += 1
            return False
    
    def get_stats(self) -> dict:
        """Get receiver statistics."""
        return {
            'packet_count': self.packet_count,
            'error_count': self.error_count,
            'buffer_size': len(self.packet_buffer),
            'buffer_capacity': self.buffer_size
        }
