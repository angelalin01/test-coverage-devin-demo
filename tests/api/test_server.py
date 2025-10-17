from datetime import datetime
from fastapi.testclient import TestClient

from api.server import create_app, StatusAPI


class TestStatusAPI:
    def test_init_creates_components(self):
        api = StatusAPI()
        assert api.receiver is not None
        assert api.processor is not None
        assert api.readiness_computer is not None
    
    def test_submit_valid_packet_returns_success(self):
        api = StatusAPI()
        packet_data = {
            "packet_id": "TEST-001",
            "timestamp": datetime.now().isoformat(),
            "source": "test_source",
            "milestone": "engine_chill",
            "data": {"status": "in_progress"}
        }
        from api.server import PacketSubmission
        submission = PacketSubmission(**packet_data)
        result = api.submit_packet(submission)
        assert result["status"] == "accepted"
        assert result["packet_id"] == "TEST-001"
    
    def test_get_readiness_returns_launch_readiness(self):
        api = StatusAPI()
        readiness = api.get_readiness()
        assert readiness.level is not None
        assert isinstance(readiness.ready_milestones, list)


class TestCreateApp:
    def test_create_app_returns_fastapi_instance(self):
        from fastapi import FastAPI
        app = create_app()
        assert isinstance(app, FastAPI)
        assert app.title == "Telemetry Status Service"
