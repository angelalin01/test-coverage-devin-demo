import asyncio
import pytest
from datetime import datetime
from ingestion.receiver import TelemetryReceiver
from ingestion.packet import TelemetryPacket

@pytest.mark.asyncio
async def test_receive_packet_async_retries_up_to_three_and_succeeds(monkeypatch):
    r = TelemetryReceiver(buffer_size=5)
    pkt = TelemetryPacket(
        packet_id="PKT-RTRY-1",
        timestamp=datetime.utcnow(),
        source="gs",
        milestone="engine_chill",
        data={"x": 1},
    )
    attempts = {"count": 0}

    from ingestion import receiver as receiver_mod

    def fake_validate(packet):
        attempts["count"] += 1
        return attempts["count"] >= 3

    monkeypatch.setattr(receiver_mod, "validate_packet", fake_validate)

    async def fast_sleep(_):
        return None

    monkeypatch.setattr(asyncio, "sleep", fast_sleep)

    ok = await r.receive_packet_async(pkt)
    assert ok is True
    assert attempts["count"] == 3
    assert r.packet_count == 1
    assert len(r.packet_buffer) == 1

@pytest.mark.asyncio
async def test_receive_packet_async_exception_increments_error_and_returns_false(monkeypatch):
    r = TelemetryReceiver(buffer_size=5)
    pkt = TelemetryPacket(
        packet_id="PKT-EXC-1",
        timestamp=datetime.utcnow(),
        source="gs",
        milestone="engine_chill",
        data={"x": 1},
    )

    def boom(_):
        raise RuntimeError("ingestion failure")

    monkeypatch.setattr(TelemetryReceiver, "receive_packet", boom)

    async def fast_sleep(_):
        return None

    monkeypatch.setattr(asyncio, "sleep", fast_sleep)

    ok = await r.receive_packet_async(pkt)
    assert ok is False
    assert r.error_count == 1
