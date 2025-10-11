import pytest
from datetime import datetime, timedelta

from status.aggregator import StatusAggregator
from processors.milestone_processor import MilestoneProcessor, MilestoneState, MilestoneStatus
from ingestion.packet import TelemetryPacket


class TestStatusAggregator:
    
    @pytest.fixture
    def aggregator(self):
        return StatusAggregator(retention_hours=24)
    
    @pytest.fixture
    def processor(self):
        return MilestoneProcessor()
    
    def test_initialization(self, aggregator):
        assert aggregator.retention_hours == 24
        assert len(aggregator.status_history) == 0
        assert len(aggregator.snapshot_timestamps) == 0
    
    def test_capture_snapshot(self, aggregator, processor):
        statuses = processor.get_all_statuses()
        
        aggregator.capture_snapshot(statuses)
        
        assert len(aggregator.status_history) == 1
        assert len(aggregator.snapshot_timestamps) == 1
        assert "engine_chill" in aggregator.status_history[0]
    
    def test_capture_multiple_snapshots(self, aggregator, processor):
        for i in range(3):
            statuses = processor.get_all_statuses()
            aggregator.capture_snapshot(statuses)
        
        assert len(aggregator.status_history) == 3
        assert len(aggregator.snapshot_timestamps) == 3
    
    def test_get_milestone_history(self, aggregator, processor):
        packet1 = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"progress": 25.0}
        )
        processor.process_packet(packet1)
        aggregator.capture_snapshot(processor.get_all_statuses())
        
        packet2 = TelemetryPacket(
            packet_id="PKT-002",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"progress": 50.0}
        )
        processor.process_packet(packet2)
        aggregator.capture_snapshot(processor.get_all_statuses())
        
        history = aggregator.get_milestone_history("engine_chill")
        
        assert len(history) == 2
        assert all(status.milestone == "engine_chill" for status in history)
    
    def test_get_milestone_history_not_in_snapshot(self, aggregator, processor):
        aggregator.capture_snapshot(processor.get_all_statuses())
        
        history = aggregator.get_milestone_history("engine_chill")
        
        assert len(history) == 1
    
    def test_get_average_progress(self, aggregator, processor):
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="fuel_load",
            data={"progress": 50.0}
        )
        processor.process_packet(packet)
        aggregator.capture_snapshot(processor.get_all_statuses())
        aggregator.capture_snapshot(processor.get_all_statuses())
        
        avg_progress = aggregator.get_average_progress("fuel_load")
        
        assert avg_progress == 50.0
    
    def test_get_average_progress_no_history(self, aggregator):
        avg_progress = aggregator.get_average_progress("engine_chill")
        
        assert avg_progress == 0.0
    
    def test_get_status_at_time(self, aggregator, processor):
        timestamp1 = datetime.now()
        packet1 = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=timestamp1,
            source="ground_station_1",
            milestone="pressurization",
            data={"status": "in_progress"}
        )
        processor.process_packet(packet1)
        aggregator.capture_snapshot(processor.get_all_statuses())
        
        query_time = timestamp1 + timedelta(seconds=1)
        status = aggregator.get_status_at_time(query_time)
        
        assert status is not None
        assert "pressurization" in status
    
    def test_get_status_at_time_no_snapshots(self, aggregator):
        status = aggregator.get_status_at_time(datetime.now())
        
        assert status is None
    
    def test_get_completion_timeline(self, aggregator, processor):
        milestones = ["engine_chill", "fuel_load", "pressurization"]
        
        for milestone in milestones:
            packet = TelemetryPacket(
                packet_id=f"PKT-{milestone}",
                timestamp=datetime.now(),
                source="ground_station_1",
                milestone=milestone,
                data={"status": "complete"}
            )
            processor.process_packet(packet)
            aggregator.capture_snapshot(processor.get_all_statuses())
        
        timeline = aggregator.get_completion_timeline()
        
        assert len(timeline) == 3
        assert "engine_chill" in timeline
        assert "fuel_load" in timeline
        assert "pressurization" in timeline
        assert all(isinstance(v, datetime) for v in timeline.values())
    
    def test_get_completion_timeline_no_completions(self, aggregator, processor):
        aggregator.capture_snapshot(processor.get_all_statuses())
        
        timeline = aggregator.get_completion_timeline()
        
        assert len(timeline) == 0
    
    def test_get_completion_timeline_partial(self, aggregator, processor):
        packet = TelemetryPacket(
            packet_id="PKT-001",
            timestamp=datetime.now(),
            source="ground_station_1",
            milestone="engine_chill",
            data={"status": "complete"}
        )
        processor.process_packet(packet)
        aggregator.capture_snapshot(processor.get_all_statuses())
        
        timeline = aggregator.get_completion_timeline()
        
        assert len(timeline) == 1
        assert "engine_chill" in timeline


class TestSnapshotRetention:
    
    @pytest.fixture
    def aggregator_short_retention(self):
        return StatusAggregator(retention_hours=1)
    
    def test_cleanup_old_snapshots(self, aggregator_short_retention, monkeypatch):
        processor = MilestoneProcessor()
        
        old_time = datetime.now() - timedelta(hours=2)
        aggregator_short_retention.snapshot_timestamps.append(old_time)
        aggregator_short_retention.status_history.append(processor.get_all_statuses())
        
        aggregator_short_retention.capture_snapshot(processor.get_all_statuses())
        
        assert len(aggregator_short_retention.snapshot_timestamps) == 1
        assert len(aggregator_short_retention.status_history) == 1
        assert aggregator_short_retention.snapshot_timestamps[0] > old_time
    
    def test_retention_keeps_recent_snapshots(self, aggregator_short_retention):
        processor = MilestoneProcessor()
        
        for _ in range(3):
            aggregator_short_retention.capture_snapshot(processor.get_all_statuses())
        
        assert len(aggregator_short_retention.snapshot_timestamps) == 3
        assert len(aggregator_short_retention.status_history) == 3
    
    def test_custom_retention_period(self):
        aggregator = StatusAggregator(retention_hours=48)
        
        assert aggregator.retention_hours == 48
