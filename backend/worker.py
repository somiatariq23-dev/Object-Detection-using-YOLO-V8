import time
import logging
import signal
import sys
from backend.core.logging_config import logger
from backend.services.queue_service import queue_service
from backend.services.video_processing_runner import process_video_file
from backend.core.device_manager import device_manager

# Set logger name
logger = logging.getLogger("app.worker")

# Flag to handle clean exits
running = True

def handle_signal(signum, frame):
    global running
    logger.info("Termination signal received. Shutting down worker gracefully...")
    running = False

# Register signal handlers for clean terminations (e.g. Docker shutdown)
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def main():
    global running
    logger.info("Starting Redis Video Analytics Worker...")
    
    # 1. Print current system hardware device information
    device_manager.print_device_info()
    
    # Keep checking Redis connection on startup
    reconnect_attempts = 0
    while not queue_service.redis_enabled and running:
        reconnect_attempts += 1
        logger.warning(f"Redis is not available yet. Retry attempt {reconnect_attempts} in 5 seconds...")
        time.sleep(5)
        queue_service.connect()
        
    if not running:
        logger.info("Worker stopped before running.")
        return

    logger.info("Worker is ready. Waiting for video processing jobs in Redis queue...")
    
    while running:
        try:
            # blpop has a built-in timeout, so this will block and release CPU
            job = queue_service.fetch_next_job()
            
            if job:
                job_id = job.get("job_id")
                filepath = job.get("filepath")
                options = job.get("options", {
                    "draw_tracking": True,
                    "draw_heatmap": True,
                    "draw_hud": True,
                    "conf_threshold": 0.25
                })
                
                logger.info(f"Picked up job {job_id} from Redis. Starting processing...")
                process_video_file(job_id, filepath, options)
                logger.info(f"Finished processing job {job_id}.")
            else:
                # If fetch_next_job returned None due to timeout, just loop back
                pass
                
        except Exception as e:
            logger.error(f"Error in worker job polling loop: {e}")
            time.sleep(2)  # Avoid fast error loops

    logger.info("Worker loop terminated. Clean exit.")

if __name__ == "__main__":
    main()
