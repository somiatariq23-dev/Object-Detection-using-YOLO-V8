import os
import time
import logging
import cv2
from datetime import datetime
from pathlib import Path

from backend.config.settings import settings
from backend.services.queue_service import queue_service
from backend.services.yolo_engine import YOLOEngine
from backend.services.tracker import Tracker
from backend.analytics.analytics_manager import AnalyticsManager
from backend.analytics.heatmap_generator import HeatmapGenerator
from backend.services.video_writer import VideoWriterService
from backend.services.video_processor import VideoProcessor
from backend.streams.stream_manager import StreamManager

logger = logging.getLogger("app.video_processing_runner")

def process_video_file(job_id: str, input_path: str, options: dict = None):
    """
    Offline video processor runner.
    Processes a saved video file, annotates it, tracks objects, and saves the output.
    """
    if options is None:
        # Default options
        options = {
            "draw_tracking": True,
            "draw_heatmap": True,
            "draw_hud": True,
            "conf_threshold": 0.25
        }

    logger.info(f"Starting processing runner for job {job_id} | File: {input_path}")
    
    # Initialize state in DB
    job_data = queue_service.get_job_status(job_id)
    if not job_data:
        job_data = {
            "job_id": job_id,
            "filepath": input_path,
            "status": "processing",
            "progress": 0,
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "statistics": None,
            "output_filepath": None
        }
    else:
        job_data["status"] = "processing"
        job_data["progress"] = 0
        
    queue_service.set_job_status(job_id, job_data)
    
    # Check input file
    in_file = Path(input_path)
    if not in_file.exists():
        logger.error(f"Input file not found: {input_path}")
        job_data["status"] = "failed"
        job_data["error"] = "Input file not found."
        queue_service.set_job_status(job_id, job_data)
        return
        
    # Setup output path
    out_filename = f"result_{job_id}_{in_file.name}"
    out_filepath = settings.RESULT_DIR / out_filename
    job_data["output_filepath"] = str(out_filepath)
    
    # Initialize processing classes
    try:
        # Load engine, tracker, counter, heatmap
        yolo = YOLOEngine()
        tracker = Tracker()
        analytics = AnalyticsManager()
        
        # Read metadata using OpenCV first to get total frames for progress
        cap_meta = cv2.VideoCapture(input_path)
        total_frames = int(cap_meta.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap_meta.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap_meta.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap_meta.get(cv2.CAP_PROP_FPS)
        cap_meta.release()
        
        if total_frames <= 0:
            total_frames = 1  # prevent division by zero
            
        if fps <= 0:
            fps = 30.0

        # Initialize Stream Manager and Video Writer
        stream_mgr = StreamManager(input_path)
        writer_srv = VideoWriterService()
        
        if not stream_mgr.start_stream():
            raise RuntimeError("Could not open input video stream.")
            
        if not writer_srv.initialize_writer(str(out_filepath), width, height, fps):
            raise RuntimeError("Could not initialize output video writer.")
            
        heatmap = HeatmapGenerator(width=width, height=height)
        
        # Video Processor Pipeline
        processor = VideoProcessor(
            yolo_engine=yolo,
            tracker=tracker,
            analytics_manager=analytics,
            heatmap_generator=heatmap,
            draw_tracking=options.get("draw_tracking", True),
            draw_heatmap=options.get("draw_heatmap", True),
            draw_hud=options.get("draw_hud", True)
        )
        
        frame_idx = 0
        last_progress_update = time.time()
        
        while True:
            frame = stream_mgr.read_frame()
            if frame is None:
                # None can mean EOF or temporary error. Since it's a file, we stop on None.
                break
                
            processed = processor.process_frame(frame, conf_threshold=options.get("conf_threshold", 0.25))
            writer_srv.write_frame(processed)
            
            frame_idx += 1
            
            # Throttle database status progress updates
            if time.time() - last_progress_update > 1.0 or frame_idx == total_frames:
                progress_pct = int((frame_idx / total_frames) * 100)
                progress_pct = min(progress_pct, 99)  # 100 represents completed
                
                job_data["progress"] = progress_pct
                job_data["statistics"] = analytics.get_statistics()
                queue_service.set_job_status(job_id, job_data)
                last_progress_update = time.time()
                logger.info(f"Job {job_id} progress: {progress_pct}% ({frame_idx}/{total_frames} frames)")
                
        # Finish up
        stream_mgr.stop_stream()
        writer_srv.release()
        
        # Set final completion state
        job_data["status"] = "completed"
        job_data["progress"] = 100
        job_data["completed_at"] = datetime.utcnow().isoformat()
        job_data["statistics"] = analytics.get_statistics()
        queue_service.set_job_status(job_id, job_data)
        logger.info(f"Job {job_id} completed successfully. Output saved to {out_filepath}")
        
    except Exception as e:
        logger.exception(f"Error during video processing job {job_id}: {e}")
        job_data["status"] = "failed"
        job_data["error"] = str(e)
        queue_service.set_job_status(job_id, job_data)
