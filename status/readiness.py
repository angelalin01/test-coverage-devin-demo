from enum import Enum
from typing import List
from datetime import datetime
from pydantic import BaseModel

from processors.milestone_processor import MilestoneProcessor, MilestoneState

CRITICAL_MILESTONES = {'engine_chill', 'fuel_load', 'pressurization'}


class ReadinessLevel(str, Enum):
    """Overall launch readiness levels."""
    NOT_READY = "not_ready"
    PARTIAL = "partial"
    READY = "ready"
    SCRUBBED = "scrubbed"


class LaunchReadiness(BaseModel):
    """Overall launch readiness status."""
    level: ReadinessLevel
    ready_milestones: List[str] = []
    pending_milestones: List[str] = []
    failed_milestones: List[str] = []
    overall_progress: float = 0.0
    message: str = ""


class ReadinessComputer:
    """Computes overall launch readiness from milestone statuses."""
    
    def __init__(self, processor: MilestoneProcessor):
        self.processor = processor
    
    def compute_readiness(self) -> LaunchReadiness:
        """Compute overall launch readiness from current milestone states."""
        all_statuses = self.processor.get_all_statuses()
        
        ready = []
        pending = []
        failed = []
        
        for milestone, status in all_statuses.items():
            if status.state == MilestoneState.COMPLETE:
                ready.append(milestone)
            elif status.state == MilestoneState.FAILED:
                failed.append(milestone)
            else:
                pending.append(milestone)
        
        total = len(all_statuses)
        overall_progress = (len(ready) / total * 100) if total > 0 else 0.0
        
        critical_failed = any(m in CRITICAL_MILESTONES for m in failed)
        critical_ready = all(m in ready for m in CRITICAL_MILESTONES if m in all_statuses)
        
        if critical_failed:
            level = ReadinessLevel.SCRUBBED
            message = f"Launch scrubbed: {', '.join(failed)}"
        elif not pending and critical_ready:
            level = ReadinessLevel.READY
            message = "All systems ready for launch"
        elif critical_ready:
            level = ReadinessLevel.PARTIAL
            message = f"{len(pending)} milestones pending"
        else:
            level = ReadinessLevel.NOT_READY
            message = f"Not ready - {len(pending)} milestones pending"
        
        return LaunchReadiness(
            level=level,
            ready_milestones=ready,
            pending_milestones=pending,
            failed_milestones=failed,
            overall_progress=overall_progress,
            message=message
        )
