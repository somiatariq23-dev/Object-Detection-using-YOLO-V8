import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config.settings import settings
from backend.core.logging_config import logger
from backend.core.device_manager import device_manager
from backend.api.router import api_router
from backend.api.endpoints.websocket import router as websocket_router
from backend.services.yolo_engine import YOLOEngine

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Events
    logger.info("Starting up Multi-Source Object Detection & Video Analytics Server...")
    
    # 1. Print Device info
    device_manager.print_device_info()
    
    # 2. Pre-load YOLO Engine to download weights and cache the model in memory
    try:
        logger.info("Pre-loading YOLO model on startup...")
        _ = YOLOEngine()
        logger.info("YOLO model pre-loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to pre-load YOLO model on startup: {e}. Model will load on-demand.")
        
    yield
    
    # Shutdown Events
    logger.info("Shutting down Multi-Source Object Detection & Video Analytics Server...")
    # Stop any active stream sessions
    from backend.streams.session_manager import session_manager
    active_ids = list(session_manager.sessions.keys())
    for stream_id in active_ids:
        logger.info(f"Closing stream session: {stream_id}")
        session_manager.stop_session(stream_id)
        
    logger.info("Shutdown complete.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade FastAPI Multi-Source Object Detection & Video Analytics System using YOLOv8, OpenCV, and WebSockets.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(websocket_router, prefix="/ws")

# Serve React frontend static files if the dist folder exists
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str = ""):
        # Let API and WS routes pass through; serve index.html for everything else
        index = FRONTEND_DIST / "index.html"
        return FileResponse(str(index))
else:
    @app.get("/")
    def read_root():
        return {
            "message": "Frontend not built. Run 'python run.py' or build manually with 'cd frontend && npm run build'.",
            "docs_url": "/docs",
            "health_url": f"{settings.API_V1_STR}/health"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=False)
