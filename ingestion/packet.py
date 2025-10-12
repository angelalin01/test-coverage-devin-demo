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
