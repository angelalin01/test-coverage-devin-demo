from enum import Enum
from typing import Dict, List
from datetime import datetime
from pydantic import BaseModel

from processors.milestone_processor import MilestoneProcessor, MilestoneState, MilestoneStatus


class ReadinessLevel(str, Enum):
    """Overall launch readiness levels."""
    NOT_READY = "not_ready"
    PARTIAL = "partial"
    READY = "ready"
    HOLD = "hold"
    SCRUBBED = "scrubbed"


class LaunchReadiness(BaseModel):
    """Overall launch readiness status."""
    level: ReadinessLevel
    ready_milestones: List[str] = []
    pending_milestones: List[str] = []
    failed_milestones: List[str] = []
    overall_progress: float = 0.0
    timestamp: datetime = datetime.now()
    message: str = ""


class ReadinessComputer:
    """
    Computes overall launch readiness from milestone statuses.
    """
    
    def __init__(self, processor: MilestoneProcessor):
        self.processor = processor
        self.critical_milestones = {'engine_chill', 'fuel_load', 'pressurization'}
    
    def compute_readiness(self) -> LaunchReadiness:
        """Compute overall launch readiness from current milestone states."""
        all_statuses = self.processor.get_all_statuses()
        
        ready = []
        pending = []
        failed = []
        
        for milestone, status in all_statuses.items():
            if status.state == MilestoneState.COMPLETE:
                ready.append(milestone)
            elif status.state in [MilestoneState.FAILED, MilestoneState.ABORTED]:
                failed.append(milestone)
            else:
                pending.append(milestone)
        
        total_milestones = len(all_statuses)
        overall_progress = (len(ready) / total_milestones * 100) if total_milestones > 0 else 0.0
        
        level = self._determine_readiness_level(ready, pending, failed, all_statuses)
        message = self._generate_message(level, ready, pending, failed)
        
        return LaunchReadiness(
            level=level,
            ready_milestones=ready,
            pending_milestones=pending,
            failed_milestones=failed,
            overall_progress=overall_progress,
            timestamp=datetime.now(),
            message=message
        )
    
    def _determine_readiness_level(
        self,
        ready: List[str],
        pending: List[str],
        failed: List[str],
        all_statuses: Dict[str, MilestoneStatus]
    ) -> ReadinessLevel:
        """Determine the overall readiness level."""
        if failed:
            critical_failed = any(m in self.critical_milestones for m in failed)
            if critical_failed:
                return ReadinessLevel.SCRUBBED
            return ReadinessLevel.HOLD
        
        critical_ready = all(
            m in ready for m in self.critical_milestones
            if m in all_statuses
        )
        
        if not pending and critical_ready:
            return ReadinessLevel.READY
        
        if critical_ready:
            return ReadinessLevel.PARTIAL
        
        return ReadinessLevel.NOT_READY
    
    def _generate_message(self, level: ReadinessLevel, ready: List[str], 
                         pending: List[str], failed: List[str]) -> str:
        """Generate a human-readable status message."""
        if level == ReadinessLevel.READY:
            return "All systems ready for launch"
        elif level == ReadinessLevel.SCRUBBED:
            return f"Launch scrubbed due to critical failures: {', '.join(failed)}"
        elif level == ReadinessLevel.HOLD:
            return f"Launch on hold: {', '.join(failed)}"
        return f"Not ready - {len(pending)} milestones pending"
