from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, field_validator

VALID_MILESTONES = {'engine_chill', 'fuel_load', 'pressurization', 'terminal_count', 'ignition', 'liftoff'}


class TelemetryPacket(BaseModel):
    """Represents a ground telemetry packet from launch operations."""
    packet_id: str
    timestamp: datetime
    source: str
    milestone: str
    data: Dict[str, Any] = {}
    sequence_number: Optional[int] = None
    
    @field_validator('milestone')
    @classmethod
    def validate_milestone(cls, v: str) -> str:
        if v not in VALID_MILESTONES:
            raise ValueError(f"Invalid milestone: {v}")
        return v


def validate_packet(packet: TelemetryPacket) -> bool:
    """Validate a telemetry packet has required data."""
    return bool(packet.packet_id and packet.data)
