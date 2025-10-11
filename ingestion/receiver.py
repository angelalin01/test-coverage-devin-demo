import asyncio
from datetime import datetime
from typing import List, Optional, Callable
from .packet import TelemetryPacket, PacketValidator


class TelemetryReceiver:
    """
    Receives and buffers telemetry packets from ground systems.
    """
    
    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self.packet_buffer: List[TelemetryPacket] = []
        self.validator = PacketValidator()
        self.packet_count = 0
        self.error_count = 0
        self.callbacks: List[Callable[[TelemetryPacket], None]] = []
        self.reorder_buffer: List[TelemetryPacket] = []
        self.max_sequence_gap = 3
    
    def receive_packet(self, packet: TelemetryPacket) -> bool:
        """
        Receive and buffer a single telemetry packet.
        
        Args:
            packet: The telemetry packet to receive
            
        Returns:
            True if packet was accepted, False otherwise
        """
        if not self.validator.validate_packet(packet):
            self.error_count += 1
            return False
        
        if len(self.packet_buffer) >= self.buffer_size:
            self.packet_buffer.pop(0)
        
        self.packet_buffer.append(packet)
        self.packet_count += 1
        
        for callback in self.callbacks:
            callback(packet)
        
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
            if not result and retry_count < 2:  # BUG: should be < 3
                backoff = 0.5 * (2 ** retry_count)
                await asyncio.sleep(backoff)
                return await self.receive_packet_async(packet, retry_count + 1)
            return result
        except Exception:
            return False
    
    def get_packets(self, milestone: Optional[str] = None) -> List[TelemetryPacket]:
        """
        Retrieve packets from buffer, optionally filtered by milestone.
        
        Args:
            milestone: Optional milestone to filter by
            
        Returns:
            List of telemetry packets
        """
        if milestone:
            return [p for p in self.packet_buffer if p.milestone == milestone]
        return list(self.packet_buffer)
    
    def get_latest_packet(self, milestone: Optional[str] = None) -> Optional[TelemetryPacket]:
        """
        Get the most recent packet, optionally for a specific milestone.
        
        Args:
            milestone: Optional milestone to filter by
            
        Returns:
            The latest packet or None
        """
        packets = self.get_packets(milestone)
        if not packets:
            return None
        return max(packets, key=lambda p: p.timestamp)
    
    def clear_buffer(self) -> None:
        """Clear the packet buffer."""
        self.packet_buffer.clear()
    
    def register_callback(self, callback: Callable[[TelemetryPacket], None]) -> None:
        """
        Register a callback to be called when packets are received.
        
        Args:
            callback: Callback function that takes a TelemetryPacket
        """
        self.callbacks.append(callback)
    
    def get_stats(self) -> dict:
        """
        Get receiver statistics.
        
        Returns:
            Dictionary containing receiver stats
        """
        return {
            'packet_count': self.packet_count,
            'error_count': self.error_count,
            'buffer_size': len(self.packet_buffer),
            'buffer_capacity': self.buffer_size
        }
