from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel

from ingestion.packet import TelemetryPacket

MILESTONES = ['engine_chill', 'fuel_load', 'pressurization', 'terminal_count', 'ignition', 'liftoff']


class MilestoneState(str, Enum):
    """Possible states for a launch milestone."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


class MilestoneStatus(BaseModel):
    """Status information for a milestone."""
    milestone: str
    state: MilestoneState
    progress_percent: float = 0.0
    last_update: Optional[datetime] = None
    error_message: Optional[str] = None


class MilestoneProcessor:
    """Processes telemetry packets and updates milestone states."""
    
    def __init__(self):
        self.milestone_states: Dict[str, MilestoneStatus] = {
            m: MilestoneStatus(milestone=m, state=MilestoneState.NOT_STARTED) 
            for m in MILESTONES
        }
    
    def process_packet(self, packet: TelemetryPacket) -> bool:
        """Process a telemetry packet and update milestone state."""
        if packet.milestone not in self.milestone_states:
            return False
        
        status = self.milestone_states[packet.milestone]
        status.last_update = packet.timestamp
        
        if 'status' in packet.data:
            status_value = packet.data['status']
            if status_value == 'complete':
                status.state = MilestoneState.COMPLETE
                status.progress_percent = 100.0
            elif status_value == 'in_progress':
                status.state = MilestoneState.IN_PROGRESS
            elif status_value == 'failed':
                status.state = MilestoneState.FAILED
                status.error_message = packet.data.get('error', 'Unknown error')
        
        if 'progress' in packet.data:
            status.progress_percent = float(packet.data['progress'])
            if status.progress_percent > 0 and status.state == MilestoneState.NOT_STARTED:
                status.state = MilestoneState.IN_PROGRESS
        
        return True
    
    def get_all_statuses(self) -> Dict[str, MilestoneStatus]:
        """Get all milestone statuses."""
        return dict(self.milestone_states)
