import asyncio
import pytest
from datetime import datetime, timezone

from ingestion.receiver import TelemetryReceiver
from ingestion.packet import TelemetryPacket


class TestTelemetryReceiverPhase2:
    @pytest.mark.asyncio
    async def test_async_retries_up_to_three_then_succeeds(self, monkeypatch):
        receiver = TelemetryReceiver()

        attempts = {"count": 0}

        def fake_receive(pkt):
            attempts["count"] += 1
            return attempts["count"] >= 4  # False for 1..3, True on 4th attempt

        async def no_sleep(_):
            return None

        monkeypatch.setattr(receiver, "receive_packet", fake_receive)
        monkeypatch.setattr(asyncio, "sleep", no_sleep)

        pkt = TelemetryPacket(
            packet_id="R-1",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="engine_chill",
            data={"ok": True},
        )
        result = await receiver.receive_packet_async(pkt)
        assert result is True
        assert attempts["count"] == 4  # initial + 3 retries

    @pytest.mark.asyncio
    async def test_async_exception_increments_error_count(self, monkeypatch):
        receiver = TelemetryReceiver()

        def boom(_):
            raise RuntimeError("transient failure")

        async def no_sleep(_):
            return None

        monkeypatch.setattr(receiver, "receive_packet", boom)
        monkeypatch.setattr(asyncio, "sleep", no_sleep)

        pkt = TelemetryPacket(
            packet_id="R-2",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="fuel_load",
            data={"x": 1},
        )
        before = receiver.error_count
        ok = await receiver.receive_packet_async(pkt)
        assert ok is False
        assert receiver.error_count == before + 1

    def test_sequence_gap_logic_leq3_accepted_gt3_rejected(self):
        receiver = TelemetryReceiver()
        pkt1 = TelemetryPacket(
            packet_id="S-1",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="engine_chill",
            data={"a": 1},
            sequence_number=1,
        )
        pkt2_ok = TelemetryPacket(
            packet_id="S-2",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="engine_chill",
            data={"a": 2},
            sequence_number=4,  # gap = 3 (<= max)
        )
        pkt2_bad = TelemetryPacket(
            packet_id="S-3",
            timestamp=datetime.now(timezone.utc),
            source="gs",
            milestone="engine_chill",
            data={"a": 3},
            sequence_number=8,  # gap = 7 (> max 3)
        )

        assert receiver.receive_packet(pkt1) is True
        before_err = receiver.error_count
        assert receiver.receive_packet(pkt2_ok) is True
        assert receiver.receive_packet(pkt2_bad) is False
        assert receiver.error_count == before_err + 1
