import pytest
from datetime import datetime, timezone
from api.server import StatusAPI, PacketSubmission
from pydantic import ValidationError


class TestStatusAPI:
    def test_submit_valid_packet_returns_201_like_response(self):
        api = StatusAPI()
        packet = PacketSubmission(
            packet_id="PKT-001",
            timestamp=datetime.now(timezone.utc),
            source="ground_station_1",
            milestone="engine_chill",
            data={"status": "in_progress", "progress": 10.0}
        )
        resp = api.submit_packet(packet)
        assert resp["status"] == "accepted"
        assert resp["packet_id"] == "PKT-001"

    def test_submit_invalid_packet_raises_400(self):
        from fastapi import HTTPException
        api = StatusAPI()
        packet = PacketSubmission(
            packet_id="PKT-002",
            timestamp=datetime.now(timezone.utc),
            source="ground_station_1",
            milestone="engine_chill",
            data={}
        )
        with pytest.raises(HTTPException) as exc:
            api.submit_packet(packet)
        assert exc.value.status_code == 400
        assert "Invalid packet data" in exc.value.detail

    def test_readiness_happy_path(self):
        api = StatusAPI()
        for m in ["engine_chill", "fuel_load", "pressurization"]:
            packet = PacketSubmission(
                packet_id=f"PKT-{m}",
                timestamp=datetime.now(timezone.utc),
                source="gs",
                milestone=m,
                data={"status": "complete", "progress": 100.0}
            )
            api.submit_packet(packet)
        readiness = api.get_readiness()
        assert readiness.level.value in {"partial", "ready", "not_ready", "scrubbed"}
        assert set(readiness.ready_milestones) >= {"engine_chill", "fuel_load", "pressurization"}
