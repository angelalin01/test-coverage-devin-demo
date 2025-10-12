"""Test utilities for telemetry status service."""
import asyncio
from datetime import datetime
from typing import Dict, Any

from ingestion.packet import TelemetryPacket


def create_test_packet(
    packet_id: str = "TEST-001",
    milestone: str = "engine_chill",
    data: Dict[str, Any] = None,
    source: str = "test_source",
    sequence_number: int = None
) -> TelemetryPacket:
    """Factory function for creating test telemetry packets."""
    if data is None:
        data = {"status": "in_progress"}
    
    return TelemetryPacket(
        packet_id=packet_id,
        timestamp=datetime.now(),
        source=source,
        milestone=milestone,
        data=data,
        sequence_number=sequence_number
    )


def run_async(coro):
    """Helper to run async functions in tests."""
    return asyncio.get_event_loop().run_until_complete(coro)
