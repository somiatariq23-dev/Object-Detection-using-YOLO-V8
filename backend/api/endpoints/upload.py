import os
import uuid
import logging
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel

from backend.config.settings import settings
from backend.streams.session_manager import session_manager

router = APIRouter()
logger = logging.getLogger("app.api.upload")

class UploadResponse(BaseModel):
    stream_id: str
    filename: str
    status: str

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_video(file: UploadFile = File(...)):
    """
    Uploads a video file and immediately starts a live stream session on it.
    Returns a stream_id — connect via WebSocket /ws/stream/{stream_id} for real-time frames.
    """
    filename = file.filename
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{ext}'. Supported: {settings.ALLOWED_EXTENSIONS}"
        )

    file_id = str(uuid.uuid4())
    dest_path = settings.UPLOAD_DIR / f"{file_id}.{ext}"

    bytes_written = 0
    try:
        async with aiofiles.open(dest_path, "wb") as out_file:
            while chunk := await file.read(1024 * 1024):
                bytes_written += len(chunk)
                if bytes_written > settings.MAX_UPLOAD_SIZE:
                    await out_file.close()
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
                        detail=f"File exceeds {settings.MAX_UPLOAD_SIZE // (1024*1024)}MB limit."
                    )
                await out_file.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving upload: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(status_code=500, detail="Error saving file.")

    # Start a live stream session on the saved file — same pipeline as webcam/RTSP
    stream_id = session_manager.start_session(str(dest_path))
    logger.info(f"Upload '{filename}' saved, live stream session started: {stream_id}")

    return UploadResponse(stream_id=stream_id, filename=filename, status="streaming")
