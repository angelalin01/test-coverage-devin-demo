from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class TelemetryPacket(BaseModel):
    """
    Represents a ground telemetry packet from launch operations.
    """
    packet_id: str = Field(..., description="Unique packet identifier")
    timestamp: datetime = Field(..., description="Packet timestamp")
    source: str = Field(..., description="Telemetry source system")
    milestone: str = Field(..., description="Launch milestone identifier")
    data: Dict[str, Any] = Field(default_factory=dict, description="Telemetry data payload")
    sequence_number: Optional[int] = Field(None, description="Packet sequence number")
    
    @field_validator('milestone')
    @classmethod
    def validate_milestone(cls, v: str) -> str:
        valid_milestones = {
            'engine_chill',
            'fuel_load',
            'pressurization',
            'terminal_count',
            'ignition',
            'liftoff'
        }
        if v not in valid_milestones:
            raise ValueError(f"Invalid milestone: {v}")
        return v
    
    def is_valid(self) -> bool:
        """Check if packet has valid structure and required fields."""
        return bool(self.packet_id and self.timestamp and self.source and self.milestone)
    
    def get_metric_value(self, metric_name: str) -> Optional[Any]:
        """Extract a specific metric value from packet data."""
        return self.data.get(metric_name)


class PacketValidator:
    """
    Validates telemetry packets for correctness and completeness.
    """
    
    @staticmethod
    def validate_packet(packet: TelemetryPacket) -> bool:
        """
        Validate a telemetry packet.
        
        Args:
            packet: The telemetry packet to validate
            
        Returns:
            True if packet is valid, False otherwise
        """
        if not packet.is_valid():
            return False
        
        if not packet.data:
            return False
        
        return True
    
    @staticmethod
    def validate_sequence(packets: list[TelemetryPacket]) -> bool:
        """
        Validate that a sequence of packets is in order.
        
        Args:
            packets: List of telemetry packets
            
        Returns:
            True if packets are in valid sequence
        """
        if not packets:
            return True
        
        for i in range(1, len(packets)):
            if packets[i].sequence_number is None or packets[i-1].sequence_number is None:
                continue
            
            if packets[i].sequence_number <= packets[i-1].sequence_number:
                return False
        
        return True
    
    @staticmethod
    def detect_duplicates(packets: list[TelemetryPacket]) -> list[str]:
        """
        Detect duplicate packets in a sequence.
        
        Args:
            packets: List of telemetry packets
            
        Returns:
            List of duplicate packet IDs
        """
        seen_ids = set()
        duplicates = []
        
        for packet in packets:
            if packet.packet_id in seen_ids:
                duplicates.append(packet.packet_id)
            else:
                seen_ids.add(packet.packet_id)
        
        return duplicates
