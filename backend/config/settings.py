import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Multi-Source Object Detection & Video Analytics"
    API_V1_STR: str = "/api/v1"
    
    # CORS Origins
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"
    ]
    
    # Storage Paths
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    RESULT_DIR: Path = BASE_DIR / "results"
    LOG_DIR: Path = BASE_DIR / "logs"
    WEIGHTS_DIR: Path = BASE_DIR / "weights"
    
    # Model Configurations
    MODEL_NAME: str = "yolov8n.pt"
    
    # Redis Queue Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_QUEUE_NAME: str = "video_processing_queue"
    
    # File limits
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = ["mp4", "avi", "mov"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Ensure directories exist
for directory in [settings.UPLOAD_DIR, settings.RESULT_DIR, settings.LOG_DIR, settings.WEIGHTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
