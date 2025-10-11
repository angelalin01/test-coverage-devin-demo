from typing import Dict, List, Optional
from datetime import datetime, timedelta

from processors.milestone_processor import MilestoneStatus


class StatusAggregator:
    """
    Aggregates and stores milestone status history.
    """
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.status_history: List[Dict[str, MilestoneStatus]] = []
        self.snapshot_timestamps: List[datetime] = []
    
    def capture_snapshot(self, statuses: Dict[str, MilestoneStatus]) -> None:
        """
        Capture a snapshot of current milestone statuses.
        
        Args:
            statuses: Dictionary of current milestone statuses
        """
        self.status_history.append(dict(statuses))
        self.snapshot_timestamps.append(datetime.now())
        self._cleanup_old_snapshots()
    
    def _cleanup_old_snapshots(self) -> None:
        """Remove snapshots older than retention period."""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        while self.snapshot_timestamps and self.snapshot_timestamps[0] < cutoff_time:
            self.snapshot_timestamps.pop(0)
            self.status_history.pop(0)
    
    def get_status_at_time(self, timestamp: datetime) -> Optional[Dict[str, MilestoneStatus]]:
        """
        Get status snapshot closest to a specific time.
        
        Args:
            timestamp: Target timestamp
            
        Returns:
            Status snapshot or None if not available
        """
        if not self.snapshot_timestamps:
            return None
        
        closest_idx = min(
            range(len(self.snapshot_timestamps)),
            key=lambda i: abs((self.snapshot_timestamps[i] - timestamp).total_seconds())
        )
        
        return self.status_history[closest_idx]
    
    def get_milestone_history(self, milestone: str) -> List[MilestoneStatus]:
        """
        Get history of a specific milestone.
        
        Args:
            milestone: Milestone identifier
            
        Returns:
            List of milestone status snapshots over time
        """
        history = []
        for snapshot in self.status_history:
            if milestone in snapshot:
                history.append(snapshot[milestone])
        return history
    
    def get_completion_timeline(self) -> Dict[str, Optional[datetime]]:
        """
        Get timeline of when each milestone was completed.
        
        Returns:
            Dictionary mapping milestone to completion time
        """
        timeline = {}
        
        for snapshot in self.status_history:
            for milestone, status in snapshot.items():
                if milestone not in timeline and status.state.value == "complete":
                    timeline[milestone] = status.last_update
        
        return timeline
    
    def get_average_progress(self, milestone: str) -> float:
        """
        Get average progress for a milestone over retained history.
        
        Args:
            milestone: Milestone identifier
            
        Returns:
            Average progress percentage
        """
        history = self.get_milestone_history(milestone)
        if not history:
            return 0.0
        
        return sum(s.progress_percent for s in history) / len(history)
