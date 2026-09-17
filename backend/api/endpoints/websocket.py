import asyncio
import logging
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status

from backend.streams.session_manager import session_manager

router = APIRouter()
logger = logging.getLogger("app.api.websocket")

class ConnectionManager:
    def __init__(self):
        # Map: stream_id -> list of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, stream_id: str):
        """
        Accepts WebSocket connection and registers it under the stream ID.
        """
        await websocket.accept()
        if stream_id not in self.active_connections:
            self.active_connections[stream_id] = []
        self.active_connections[stream_id].append(websocket)
        logger.info(f"WebSocket client connected to stream {stream_id}. Active subscribers: {len(self.active_connections[stream_id])}")

    def disconnect(self, websocket: WebSocket, stream_id: str):
        """
        Unregisters the WebSocket connection from the stream.
        """
        if stream_id in self.active_connections:
            self.active_connections[stream_id].remove(websocket)
            if not self.active_connections[stream_id]:
                self.active_connections.pop(stream_id)
            logger.info(f"WebSocket client disconnected from stream {stream_id}.")

    async def broadcast(self, message: bytes, stream_id: str):
        """
        Broadcasts binary data (JPEG bytes) to all active WebSocket clients of a specific stream.
        """
        if stream_id not in self.active_connections:
            return
            
        disconnected_clients = []
        for connection in self.active_connections[stream_id]:
            try:
                await connection.send_bytes(message)
            except Exception as e:
                logger.debug(f"Failed to send message to client on stream {stream_id}: {e}")
                disconnected_clients.append(connection)
                
        # Clean up any failed connections
        for client in disconnected_clients:
            self.disconnect(client, stream_id)

manager = ConnectionManager()

@router.websocket("/stream/{stream_id}")
async def websocket_stream_endpoint(websocket: WebSocket, stream_id: str):
    """
    WebSocket endpoint that stream JPEGs of the processed video frames in real-time.
    """
    # 1. Validate stream exists
    status_data = session_manager.get_session_status(stream_id)
    if not status_data:
        # Cannot accept connection if stream is invalid
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning(f"Rejected WS connection: Stream ID {stream_id} does not exist.")
        return

    # 2. Accept and register connection
    await manager.connect(websocket, stream_id)
    
    try:
        last_frame_sent = None
        while True:
            # Check stream status in session manager
            status_data = session_manager.get_session_status(stream_id)
            if not status_data or status_data["status"] not in ["running", "starting"]:
                logger.info(f"Stream {stream_id} is no longer running. Closing WS.")
                break
                
            # Get latest frame bytes
            frame_bytes = session_manager.get_latest_frame(stream_id)
            
            if frame_bytes and frame_bytes != last_frame_sent:
                # Send binary JPEG bytes
                await websocket.send_bytes(frame_bytes)
                last_frame_sent = frame_bytes
                
            # Throttle the polling loop to prevent high CPU usage (approx 60fps max)
            await asyncio.sleep(0.016)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, stream_id)
    except Exception as e:
        logger.error(f"WebSocket processing error on stream {stream_id}: {e}")
        manager.disconnect(websocket, stream_id)
