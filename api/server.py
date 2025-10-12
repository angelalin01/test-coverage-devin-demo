from datetime import datetime
from typing import Dict
from fastapi import FastAPI, HTTPException, status as http_status
from pydantic import BaseModel

from ingestion.packet import TelemetryPacket
from ingestion.receiver import TelemetryReceiver
from processors.milestone_processor import MilestoneProcessor
from status.readiness import ReadinessComputer, LaunchReadiness


class PacketSubmission(BaseModel):
    """Request model for submitting telemetry packets."""
    packet_id: str
    timestamp: datetime
    source: str
    milestone: str
    data: Dict


class StatusAPI:
    """API handler for telemetry status service."""
    
    def __init__(self):
        self.receiver = TelemetryReceiver()
        self.processor = MilestoneProcessor()
        self.readiness_computer = ReadinessComputer(self.processor)
    
    def submit_packet(self, packet_data: PacketSubmission) -> Dict:
        """Submit a telemetry packet for processing."""
        packet = TelemetryPacket(
            packet_id=packet_data.packet_id,
            timestamp=packet_data.timestamp,
            source=packet_data.source,
            milestone=packet_data.milestone,
            data=packet_data.data
        )
        
        if not self.receiver.receive_packet(packet):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid packet data"
            )
        
        self.processor.process_packet(packet)
        return {"status": "accepted", "packet_id": packet.packet_id}
    
    def get_readiness(self) -> LaunchReadiness:
        """Get overall launch readiness."""
        return self.readiness_computer.compute_readiness()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Telemetry Status Service",
        description="Ground telemetry processing for launch operations",
        version="0.1.0"
    )
    
    api = StatusAPI()
    
    @app.post("/packets", status_code=http_status.HTTP_201_CREATED)
    async def submit_packet(packet: PacketSubmission):
        return api.submit_packet(packet)
    
    @app.get("/readiness")
    async def get_readiness():
        return api.get_readiness()
    
    return app
