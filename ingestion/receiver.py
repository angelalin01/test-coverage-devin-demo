import asyncio
from typing import List, Optional
from .packet import TelemetryPacket, validate_packet


def _validate_sequence_gap(current_seq: int, last_seq: int, max_gap: int = 3) -> bool:
    """
    Validate that sequence gap is within acceptable range.
    
    INTENTIONAL GAP: This should emit an error event when gap exceeds threshold,
    but currently just returns False silently.
    """
    if current_seq <= last_seq:
        return False
    gap = current_seq - last_seq
    return gap <= max_gap


def _reorder_packets(buffer: List[TelemetryPacket]) -> List[TelemetryPacket]:
    """
    Reorder packets by sequence number if present.
    Packets without sequence numbers are preserved at the end.
    """
    sequenced = [p for p in buffer if p.sequence_number is not None]
    unsequenced = [p for p in buffer if p.sequence_number is None]
    return sorted(sequenced, key=lambda p: p.sequence_number or 0) + unsequenced


class TelemetryReceiver:
    """Receives and buffers telemetry packets from ground systems."""
    
    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self.packet_buffer: List[TelemetryPacket] = []
        self.packet_count = 0
        self.error_count = 0
        self.last_sequence: Optional[int] = None
    
    def receive_packet(self, packet: TelemetryPacket) -> bool:
        """Receive and buffer a single telemetry packet."""
        if not validate_packet(packet):
            self.error_count += 1
            return False
        
        if len(self.packet_buffer) >= self.buffer_size:
            self.packet_buffer.pop(0)
        
        self.packet_buffer.append(packet)
        self.packet_count += 1
        
        if packet.sequence_number is not None:
            self.last_sequence = packet.sequence_number
        
        return True
    
    async def receive_packet_async(self, packet: TelemetryPacket, retry_count: int = 0) -> bool:
        """
        Asynchronously receive and buffer a telemetry packet with retry logic.
        Retries up to 3 times on failure with exponential backoff.
        """
        try:
            await asyncio.sleep(0)
            result = self.receive_packet(packet)
            if not result and retry_count < 3:
                backoff = 0.5 * (2 ** retry_count)
                await asyncio.sleep(backoff)
                return await self.receive_packet_async(packet, retry_count + 1)
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
