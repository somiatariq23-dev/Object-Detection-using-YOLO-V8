import logging
import os
from logging.handlers import RotatingFileHandler
from backend.config.settings import settings

def setup_logging():
    # Make sure logging dir exists
    log_dir = settings.LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"
    
    # Base configuration
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8"
            )
        ]
    )
    
    # Reduce verbose logging from third party modules
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("ultralytics").setLevel(logging.WARNING)
    
    logger = logging.getLogger("app")
    logger.info("Logging configured successfully.")
    return logger

logger = setup_logging()
