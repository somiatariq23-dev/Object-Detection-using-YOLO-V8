from fastapi import APIRouter

from backend.api.endpoints.health import router as health_router
from backend.api.endpoints.upload import router as upload_router
from backend.api.endpoints.stream import router as stream_router

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(upload_router, prefix="/video", tags=["Video Upload"])
api_router.include_router(stream_router, prefix="/stream", tags=["Live Streaming"])
