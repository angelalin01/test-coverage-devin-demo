from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, status as http_status
from pydantic import BaseModel

from ingestion.packet import TelemetryPacket
from ingestion.receiver import TelemetryReceiver
from processors.milestone_processor import MilestoneProcessor, MilestoneStatus
from status.readiness import ReadinessComputer, LaunchReadiness
from status.aggregator import StatusAggregator


class PacketSubmission(BaseModel):
    """Request model for submitting telemetry packets."""
    packet_id: str
    timestamp: datetime
    source: str
    milestone: str
    data: Dict
    sequence_number: Optional[int] = None


class StatusAPI:
    """
    API handler for telemetry status service.
    """
    
    def __init__(self):
        self.receiver = TelemetryReceiver()
        self.processor = MilestoneProcessor()
        self.readiness_computer = ReadinessComputer(self.processor)
        self.aggregator = StatusAggregator()
        
        self.receiver.register_callback(self._on_packet_received)
    
    def _on_packet_received(self, packet: TelemetryPacket) -> None:
        """Callback for when a packet is received."""
        self.processor.process_packet(packet)
    
    def submit_packet(self, packet_data: PacketSubmission) -> Dict:
        """
        Submit a telemetry packet for processing.
        
        Args:
            packet_data: Packet data to submit
            
        Returns:
            Status response
        """
        packet = TelemetryPacket(
            packet_id=packet_data.packet_id,
            timestamp=packet_data.timestamp,
            source=packet_data.source,
            milestone=packet_data.milestone,
            data=packet_data.data,
            sequence_number=packet_data.sequence_number
        )
        
        if not self.receiver.receive_packet(packet):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid packet data"
            )
        
        return {"status": "accepted", "packet_id": packet.packet_id}
    
    def get_milestone_status(self, milestone: str) -> MilestoneStatus:
        """
        Get status for a specific milestone.
        
        Args:
            milestone: Milestone identifier
            
        Returns:
            Milestone status
        """
        status = self.processor.get_milestone_status(milestone)
        if not status:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Milestone {milestone} not found"
            )
        return status
    
    def get_all_statuses(self) -> Dict[str, MilestoneStatus]:
        """
        Get all milestone statuses.
        
        Returns:
            Dictionary of all milestone statuses
        """
        return self.processor.get_all_statuses()
    
    def get_readiness(self) -> LaunchReadiness:
        """
        Get overall launch readiness.
        
        Returns:
            Launch readiness status
        """
        return self.readiness_computer.compute_readiness()
    
    def get_receiver_stats(self) -> Dict:
        """
        Get telemetry receiver statistics.
        
        Returns:
            Receiver statistics
        """
        return self.receiver.get_stats()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="Telemetry Status Service",
        description="Ground telemetry processing for launch operations",
        version="0.1.0"
    )
    
    api = StatusAPI()
    
    @app.post("/packets", status_code=http_status.HTTP_201_CREATED)
    async def submit_packet(packet: PacketSubmission):
        """Submit a telemetry packet."""
        return api.submit_packet(packet)
    
    @app.get("/milestones/{milestone}")
    async def get_milestone_status(milestone: str):
        """Get status for a specific milestone."""
        return api.get_milestone_status(milestone)
    
    @app.get("/milestones")
    async def get_all_milestones():
        """Get all milestone statuses."""
        return api.get_all_statuses()
    
    @app.get("/readiness")
    async def get_readiness():
        """Get overall launch readiness."""
        return api.get_readiness()
    
    @app.get("/stats")
    async def get_stats():
        """Get telemetry receiver statistics."""
        return api.get_receiver_stats()
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": datetime.now()}
    
    return app
