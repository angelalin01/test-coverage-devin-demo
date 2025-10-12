import pytest
from datetime import datetime, timezone
from fastapi import HTTPException

from api.server import StatusAPI, PacketSubmission
from processors.milestone_processor import MilestoneState


class TestStatusAPIPhase3:
    def test_get_milestone_status_returns_existing_milestone(self):
        api = StatusAPI()
        
        packet = PacketSubmission(
            packet_id="MS-1",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="engine_chill",
            data={"status": "complete"}
        )
        api.submit_packet(packet)
        
        status = api.get_milestone_status("engine_chill")
        
        assert status.milestone == "engine_chill"
        assert status.state == MilestoneState.COMPLETE

    def test_get_all_statuses_returns_all_milestones(self):
        api = StatusAPI()
        
        statuses = api.get_all_statuses()
        
        assert len(statuses) == 6
        expected_milestones = {
            'engine_chill', 'fuel_load', 'pressurization',
            'terminal_count', 'ignition', 'liftoff'
        }
        assert set(statuses.keys()) == expected_milestones

    def test_get_receiver_stats_returns_statistics(self):
        api = StatusAPI()
        
        packet = PacketSubmission(
            packet_id="STAT-1",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="engine_chill",
            data={"temperature": -180.5}
        )
        api.submit_packet(packet)
        
        stats = api.get_receiver_stats()
        
        assert "packet_count" in stats
        assert "error_count" in stats
        assert "buffer_size" in stats
        assert "buffer_capacity" in stats
        assert stats["packet_count"] == 1
        assert stats["buffer_size"] == 1
