from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from backend.streams.session_manager import session_manager

router = APIRouter()

class StreamOptions(BaseModel):
    draw_tracking: bool = Field(default=True, description="Enable object tracking boxes and IDs")
    draw_heatmap: bool = Field(default=False, description="Enable object density heatmap overlay")
    draw_hud: bool = Field(default=True, description="Enable statistics overlay panel on video")
    conf_threshold: float = Field(default=0.25, ge=0.0, le=1.0, description="Confidence threshold for YOLO detections")

class StreamStartRequest(BaseModel):
    source: str = Field(..., description="Webcam index (e.g. '0'), file path, or RTSP URL")
    options: Optional[StreamOptions] = None

class StreamStartResponse(BaseModel):
    stream_id: str
    status: str
    source: str

class StreamStatusResponse(BaseModel):
    stream_id: str
    status: str
    source: str
    width: int
    height: int
    fps: float
    frame_count: int
    statistics: Dict[str, Any]
    error: Optional[str] = None

class StreamStopResponse(BaseModel):
    stream_id: str
    status: str

@router.post("/start", response_model=StreamStartResponse)
def start_stream(request: StreamStartRequest):
    """
    Starts processing a new live stream (webcam, file, or RTSP stream).
    """
    options_dict = request.options.model_dump() if request.options else {
        "draw_tracking": True,
        "draw_heatmap": False,
        "draw_hud": True,
        "conf_threshold": 0.25
    }
    
    try:
        stream_id = session_manager.start_session(request.source, options_dict)
        return StreamStartResponse(
            stream_id=stream_id,
            status="starting",
            source=request.source
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start stream session: {e}"
        )

@router.get("/status/{stream_id}", response_model=StreamStatusResponse)
def get_stream_status(stream_id: str):
    """
    Fetches the operational status, FPS, and detection metrics of a stream session.
    """
    status_data = session_manager.get_session_status(stream_id)
    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stream session {stream_id} not found."
        )
    return status_data

@router.post("/stop/{stream_id}", response_model=StreamStopResponse)
def stop_stream(stream_id: str):
    """
    Stops a running stream session and releases all associated resources.
    """
    success = session_manager.stop_session(stream_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stream session {stream_id} not found or already stopped."
        )
    return StreamStopResponse(
        stream_id=stream_id,
        status="stopped"
    )
