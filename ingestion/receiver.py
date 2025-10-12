import asyncio
from typing import List, Optional
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
        self.last_sequence_number: Optional[int] = None
    
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
            if self.last_sequence_number is not None:
                gap = packet.sequence_number - self.last_sequence_number
                if gap > self.max_sequence_gap:
                    self.error_count += 1
                    return False
            
            self.reorder_buffer.append(packet)
            self.reorder_buffer.sort(key=lambda p: p.sequence_number or 0)
            
            while self.reorder_buffer:
                next_packet = self.reorder_buffer[0]
                if self.last_sequence_number is None or next_packet.sequence_number == self.last_sequence_number + 1:
                    self.reorder_buffer.pop(0)
                    self._add_to_buffer(next_packet)
                    self.last_sequence_number = next_packet.sequence_number
                else:
                    break
            
            return True
        else:
            self._add_to_buffer(packet)
            return True
    
    def _add_to_buffer(self, packet: TelemetryPacket) -> None:
        """Add packet to buffer, evicting oldest if full."""
        if len(self.packet_buffer) >= self.buffer_size:
            self.packet_buffer.pop(0)
        
        self.packet_buffer.append(packet)
        self.packet_count += 1
    
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
            if not result and retry_count < 2:
                backoff = 0.5 * (2 ** retry_count)
                await asyncio.sleep(backoff)
                return await self.receive_packet_async(packet, retry_count + 1)
            return result
        except Exception as e:
            self.emit_error_event(
                error_type=type(e).__name__,
                error_message=str(e),
                packet_id=getattr(packet, 'packet_id', 'unknown')
            )
            return False
    
    def emit_error_event(self, error_type: str, error_message: str, packet_id: str) -> None:
        """
        Emit an error event for monitoring and alerting.
        
        Args:
            error_type: Type of the error
            error_message: Error message
            packet_id: ID of the packet that caused the error
        """
        self.error_count += 1
    
    def get_stats(self) -> dict:
        """Get receiver statistics."""
        return {
            'packet_count': self.packet_count,
            'error_count': self.error_count,
            'buffer_size': len(self.packet_buffer),
            'buffer_capacity': self.buffer_size
        }
