from enum import Enum
from typing import Dict, List, Optional
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
    message: Optional[str] = None


class ReadinessComputer:
    """
    Computes overall launch readiness from milestone statuses.
    """
    
    def __init__(self, processor: MilestoneProcessor):
        self.processor = processor
        self.critical_milestones = {'engine_chill', 'fuel_load', 'pressurization'}
    
    def compute_readiness(self) -> LaunchReadiness:
        """
        Compute overall launch readiness from current milestone states.
        
        Returns:
            LaunchReadiness status
        """
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
        
        # SEEDED BUG #6: No dependency check - milestone can be marked complete even if dependencies incomplete
        # Example: liftoff could be COMPLETE even if engine_chill is still IN_PROGRESS
        # Current tests don't verify milestone ordering or dependency constraints
        # Future test needed: test_milestone_dependencies_enforced() and test_liftoff_requires_all_previous_complete()
        
        critical_ready = all(
            m in ready for m in self.critical_milestones
            if m in all_statuses
        )
        
        if not pending and critical_ready:
            return ReadinessLevel.READY
        
        if critical_ready:
            return ReadinessLevel.PARTIAL
        
        return ReadinessLevel.NOT_READY
    
    def _generate_message(
        self,
        level: ReadinessLevel,
        ready: List[str],
        pending: List[str],
        failed: List[str]
    ) -> str:
        """Generate a human-readable status message."""
        if level == ReadinessLevel.READY:
            return "All systems ready for launch"
        elif level == ReadinessLevel.SCRUBBED:
            return f"Launch scrubbed due to critical milestone failures: {', '.join(failed)}"
        elif level == ReadinessLevel.HOLD:
            return f"Launch on hold due to failures: {', '.join(failed)}"
        elif level == ReadinessLevel.PARTIAL:
            return f"Partial readiness - {len(pending)} milestones pending"
        else:
            return "Launch not ready - critical milestones incomplete"
    
    def is_go_for_launch(self) -> bool:
        """
        Check if system is go for launch.
        
        Returns:
            True if all critical milestones are complete
        """
        readiness = self.compute_readiness()
        return readiness.level == ReadinessLevel.READY
    
    def get_blocking_issues(self) -> List[str]:
        """
        Get list of issues blocking launch readiness.
        
        Returns:
            List of blocking issue descriptions
        """
        issues = []
        all_statuses = self.processor.get_all_statuses()
        
        for milestone in self.critical_milestones:
            if milestone in all_statuses:
                status = all_statuses[milestone]
                if status.state == MilestoneState.FAILED:
                    issues.append(f"{milestone}: {status.error_message or 'Failed'}")
                elif status.state != MilestoneState.COMPLETE:
                    issues.append(f"{milestone}: Not complete (state: {status.state})")
        
        return issues
