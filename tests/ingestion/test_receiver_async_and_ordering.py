import asyncio
import pytest
from datetime import datetime

from ingestion.receiver import TelemetryReceiver, _validate_sequence_gap, _reorder_packets
async def no_sleep(*_args, **_kwargs):
    return None


from ingestion.packet import TelemetryPacket


@pytest.mark.asyncio
async def test_receive_packet_async_retries_three_times_then_succeeds(monkeypatch):
    r = TelemetryReceiver()

    calls = {"count": 0}

    def fake_receive(packet):
        calls["count"] += 1
        return calls["count"] >= 4



    monkeypatch.setattr(r, "receive_packet", fake_receive)
    monkeypatch.setattr(asyncio, "sleep", no_sleep)

    pkt = TelemetryPacket(
        packet_id="A1",
        timestamp=datetime.now(),
        source="gs1",
        milestone="engine_chill",
        data={"status": "in_progress"},
    )
    result = await r.receive_packet_async(pkt)
    assert result is True
    assert calls["count"] == 4


@pytest.mark.asyncio
async def test_receive_packet_async_exception_increments_error_count(monkeypatch):
    r = TelemetryReceiver()

    def boom(_packet):
        raise RuntimeError("transient")

    monkeypatch.setattr(r, "receive_packet", boom)
    monkeypatch.setattr(asyncio, "sleep", no_sleep)

    pkt = TelemetryPacket(
        packet_id="B1",
        timestamp=datetime.now(),
        source="gs1",
        milestone="fuel_load",
        data={"status": "in_progress"},
    )
    ok = await r.receive_packet_async(pkt)
    assert ok is False
    assert r.error_count >= 1


def test_validate_sequence_gap_boundaries():
    assert _validate_sequence_gap(5, 5, 3) is False
    assert _validate_sequence_gap(4, 5, 3) is False
    assert _validate_sequence_gap(8, 6, 3) is True
    assert _validate_sequence_gap(10, 6, 3) is False


def test_reorder_preserves_unsequenced_and_sorts_sequenced():
    p_none1 = TelemetryPacket(
        packet_id="U1",
        timestamp=datetime.now(),
        source="gs1",
        milestone="engine_chill",
        data={"status": "in_progress"},
    )
    p2 = TelemetryPacket(
        packet_id="S2",
        timestamp=datetime.now(),
        source="gs1",
        milestone="engine_chill",
        data={"status": "in_progress"},
        sequence_number=2,
    )
    p1 = TelemetryPacket(
        packet_id="S1",
        timestamp=datetime.now(),
        source="gs1",
        milestone="engine_chill",
        data={"status": "in_progress"},
        sequence_number=1,
    )
    p_none2 = TelemetryPacket(
        packet_id="U2",
        timestamp=datetime.now(),
        source="gs1",
        milestone="engine_chill",
        data={"status": "in_progress"},
    )

    ordered = _reorder_packets([p_none1, p2, p1, p_none2])
    ids = [p.packet_id for p in ordered]
    assert ids == ["S1", "S2", "U1", "U2"]
