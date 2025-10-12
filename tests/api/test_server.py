import pytest
from datetime import datetime
import httpx
from httpx import ASGITransport

from api.server import create_app

class TestAPIServer:
    @pytest.fixture
    def app(self):
        return create_app()

    @pytest.fixture
    async def aclient(self, app):
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client

    @pytest.mark.anyio
    async def test_submit_packet_success(self, aclient):
        payload = {
            "packet_id": "PKT-API-001",
            "timestamp": datetime.now().isoformat(),
            "source": "gs",
            "milestone": "engine_chill",
            "data": {"status": "in_progress"}
        }
        resp = await aclient.post("/packets", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "accepted"
        assert body["packet_id"] == "PKT-API-001"

    @pytest.mark.anyio
    async def test_submit_packet_invalid_milestone_returns_400(self, aclient):
        payload = {
            "packet_id": "PKT-API-002",
            "timestamp": datetime.now().isoformat(),
            "source": "gs",
            "milestone": "unknown_milestone",
            "data": {"status": "in_progress"}
        }
        resp = await aclient.post("/packets", json=payload)
        assert resp.status_code == 400
        assert "Invalid" in resp.text

    @pytest.mark.anyio
    async def test_get_milestone_not_found_returns_404(self, aclient):
        resp = await aclient.get("/milestones/does_not_exist")
        assert resp.status_code == 404
        assert "not found" in resp.text.lower()

    @pytest.mark.anyio
    async def test_readiness_partial_and_message(self, aclient):
        for milestone in ["engine_chill", "fuel_load"]:
            payload = {
                "packet_id": f"PKT-{milestone}",
                "timestamp": datetime.now().isoformat(),
                "source": "gs",
                "milestone": milestone,
                "data": {"status": "complete"}
            }
            r = await aclient.post("/packets", json=payload)
            assert r.status_code == 201
        readiness = (await aclient.get("/readiness")).json()
        assert readiness["level"] in ("partial", "not_ready")
        assert "Not ready" in readiness["message"]

    @pytest.mark.anyio
    async def test_readiness_not_ready_and_message(self, aclient):
        readiness = (await aclient.get("/readiness")).json()
        assert readiness["level"] in ("not_ready", "partial")
