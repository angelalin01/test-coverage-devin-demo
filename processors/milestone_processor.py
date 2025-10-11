from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel

from ingestion.packet import TelemetryPacket


class MilestoneState(str, Enum):
    """Possible states for a launch milestone."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"
    ABORTED = "aborted"


class MilestoneStatus(BaseModel):
    """Status information for a milestone."""
    milestone: str
    state: MilestoneState
    progress_percent: float = 0.0
    last_update: Optional[datetime] = None
    error_message: Optional[str] = None
    metrics: Dict[str, float] = {}


class MilestoneProcessor:
    """
    Processes telemetry packets and updates milestone states.
    """
    
    def __init__(self):
        self.milestone_states: Dict[str, MilestoneStatus] = {}
        self._initialize_milestones()
    
    def _initialize_milestones(self) -> None:
        """Initialize all known milestones to NOT_STARTED state."""
        milestones = [
            'engine_chill',
            'fuel_load',
            'pressurization',
            'terminal_count',
            'ignition',
            'liftoff'
        ]
        
        for milestone in milestones:
            self.milestone_states[milestone] = MilestoneStatus(
                milestone=milestone,
                state=MilestoneState.NOT_STARTED
            )
    
    def process_packet(self, packet: TelemetryPacket) -> bool:
        """
        Process a telemetry packet and update milestone state.
        
        Args:
            packet: The telemetry packet to process
            
        Returns:
            True if packet was successfully processed
        """
        if packet.milestone not in self.milestone_states:
            return False
        
        status = self.milestone_states[packet.milestone]
        
        # SEEDED BUG #5: Duplicate packets overwrite state without checking packet_id
        # No deduplication - same packet can be processed multiple times, corrupting metrics
        # Current tests don't verify duplicate packet rejection
        # Future test needed: test_process_duplicate_packet_rejected()
        
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
        
        for key, value in packet.data.items():
            if isinstance(value, (int, float)) and key not in ['status', 'progress']:
                status.metrics[key] = float(value)
        
        return True
    
    def get_milestone_status(self, milestone: str) -> Optional[MilestoneStatus]:
        """
        Get the current status of a milestone.
        
        Args:
            milestone: The milestone identifier
            
        Returns:
            MilestoneStatus or None if milestone not found
        """
        return self.milestone_states.get(milestone)
    
    def get_all_statuses(self) -> Dict[str, MilestoneStatus]:
        """
        Get all milestone statuses.
        
        Returns:
            Dictionary of milestone statuses
        """
        return dict(self.milestone_states)
    
    def is_milestone_complete(self, milestone: str) -> bool:
        """
        Check if a milestone is complete.
        
        Args:
            milestone: The milestone identifier
            
        Returns:
            True if milestone is complete
        """
        status = self.milestone_states.get(milestone)
        return status.state == MilestoneState.COMPLETE if status else False
    
    def reset_milestone(self, milestone: str) -> bool:
        """
        Reset a milestone to NOT_STARTED state.
        
        Args:
            milestone: The milestone identifier
            
        Returns:
            True if milestone was reset
        """
        if milestone not in self.milestone_states:
            return False
        
        self.milestone_states[milestone] = MilestoneStatus(
            milestone=milestone,
            state=MilestoneState.NOT_STARTED
        )
        return True
    
    def get_completion_count(self) -> int:
        """
        Get the number of completed milestones.
        
        Returns:
            Count of completed milestones
        """
        return sum(
            1 for status in self.milestone_states.values()
            if status.state == MilestoneState.COMPLETE
        )
