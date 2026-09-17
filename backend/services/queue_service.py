import json
import logging
import redis
from typing import Dict, Any, Optional
from datetime import datetime

from backend.config.settings import settings

class QueueService:
    def __init__(self):
        self.logger = logging.getLogger("app.queue_service")
        self.redis_client = None
        self.redis_enabled = False
        
        # In-memory database fallback if Redis is not available
        self._in_memory_db: Dict[str, Dict[str, Any]] = {}
        
        self.connect()

    def connect(self):
        """
        Attempts to connect to the Redis instance.
        """
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            self.redis_enabled = True
            self.logger.info("Successfully connected to Redis. Distributed queue active.")
        except Exception as e:
            self.redis_enabled = False
            self.logger.warning(
                f"Could not connect to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT} ({e}). "
                "Using in-memory fallback for local session/job tracking."
            )

    def enqueue_job(self, job_id: str, filepath: str) -> bool:
        """
        Enqueues a video processing job.
        """
        job_data = {
            "job_id": job_id,
            "filepath": filepath,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "statistics": None,
            "output_filepath": None
        }

        # Save job status
        self.set_job_status(job_id, job_data)

        if self.redis_enabled:
            try:
                # Push job details onto the Redis queue list
                self.redis_client.rpush(settings.REDIS_QUEUE_NAME, json.dumps(job_data))
                self.logger.info(f"Enqueued job {job_id} into Redis list '{settings.REDIS_QUEUE_NAME}'")
                return True
            except Exception as e:
                self.logger.error(f"Failed to enqueue job {job_id} to Redis: {e}. Falling back to local scheduling.")
                
        # In-memory fallback
        self.logger.info(f"Enqueued job {job_id} to in-memory store.")
        return False

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves current status details of a job.
        """
        if self.redis_enabled:
            try:
                key = f"job:{job_id}"
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                self.logger.error(f"Error reading job {job_id} from Redis: {e}")
                
        return self._in_memory_db.get(job_id)

    def set_job_status(self, job_id: str, job_data: Dict[str, Any]):
        """
        Updates the job state database.
        """
        if self.redis_enabled:
            try:
                key = f"job:{job_id}"
                # Expire job state after 24 hours to keep Redis clean
                self.redis_client.setex(key, 86400, json.dumps(job_data))
                return
            except Exception as e:
                self.logger.error(f"Error writing job {job_id} to Redis: {e}")
                
        self._in_memory_db[job_id] = job_data
        
    def fetch_next_job(self) -> Optional[Dict[str, Any]]:
        """
        Pulls the next job from the queue (blocking or non-blocking).
        Used by the worker.
        """
        if self.redis_enabled:
            try:
                # Blocking pop from the queue with a 5-second timeout
                res = self.redis_client.blpop(settings.REDIS_QUEUE_NAME, timeout=5)
                if res:
                    _, payload = res
                    return json.loads(payload)
            except Exception as e:
                self.logger.error(f"Error fetching from Redis queue: {e}")
                
        return None

queue_service = QueueService()
