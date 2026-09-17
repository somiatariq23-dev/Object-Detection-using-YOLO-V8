import cv2
import uuid
import logging
import threading
import time
from typing import Dict, Any, Optional, Tuple

from backend.streams.stream_manager import StreamManager
from backend.services.yolo_engine import YOLOEngine
from backend.services.tracker import Tracker
from backend.analytics.analytics_manager import AnalyticsManager
from backend.analytics.heatmap_generator import HeatmapGenerator
from backend.services.video_processor import VideoProcessor

class StreamSessionManager:
    def __init__(self):
        self.logger = logging.getLogger("app.stream_session_manager")
        # Structure: { stream_id: { "manager": StreamManager, "thread": Thread, "status": str, "latest_frame": bytes, "statistics": dict, "source": str, "width": int, "height": int } }
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def start_session(self, source: str, options: dict = None) -> str:
        """
        Spawns a background thread to process a live video stream.
        Returns the generated stream_id (UUID).
        """
        if options is None:
            options = {
                "draw_tracking": True,
                "draw_heatmap": False,
                "draw_hud": True,
                "conf_threshold": 0.25
            }

        stream_id = str(uuid.uuid4())
        
        with self._lock:
            self.sessions[stream_id] = {
                "status": "starting",
                "source": source,
                "latest_frame": None,
                "statistics": {},
                "fps": 30.0,
                "width": 640,
                "height": 480,
                "options": options,
                "frame_count": 0,
                "error": None
            }

        # Spawn processing thread
        thread = threading.Thread(
            target=self._stream_loop,
            args=(stream_id, source, options),
            name=f"stream-thread-{stream_id}",
            daemon=True
        )
        
        with self._lock:
            self.sessions[stream_id]["thread"] = thread
            
        thread.start()
        return stream_id

    def _stream_loop(self, stream_id: str, source: str, options: dict):
        """
        Background frame-by-frame stream processor thread.
        """
        self.logger.info(f"Stream thread started for {stream_id} (source: {source})")
        
        stream_mgr = None
        yolo = None
        tracker = None
        analytics = None
        heatmap = None
        
        try:
            # 1. Initialize dependencies
            yolo = YOLOEngine()
            tracker = Tracker()
            analytics = AnalyticsManager()
            stream_mgr = StreamManager(source)
            
            if not stream_mgr.start_stream():
                raise RuntimeError(f"Could not connect to video source: {source}")
                
            w, h = stream_mgr.get_dimensions()
            fps = stream_mgr.get_fps()
            
            heatmap = HeatmapGenerator(width=w, height=h)
            
            processor = VideoProcessor(
                yolo_engine=yolo,
                tracker=tracker,
                analytics_manager=analytics,
                heatmap_generator=heatmap,
                draw_tracking=options.get("draw_tracking", True),
                draw_heatmap=options.get("draw_heatmap", False),
                draw_hud=options.get("draw_hud", True)
            )

            with self._lock:
                session = self.sessions.get(stream_id)
                if session:
                    session["status"] = "running"
                    session["width"] = w
                    session["height"] = h
                    session["fps"] = fps
                    session["manager"] = stream_mgr

            # Delay to throttle loop matching real FPS (for video files)
            frame_delay = 1.0 / fps if fps > 0 else 0.033
            
            while True:
                # Check for stop request
                with self._lock:
                    session = self.sessions.get(stream_id)
                    if not session or session["status"] == "stopping":
                        break

                start_time = time.time()
                frame = stream_mgr.read_frame()
                
                if frame is None:
                    # If it's a file, EOF is natural
                    if stream_mgr.is_file:
                        self.logger.info(f"EOF reached for local file stream {stream_id}")
                        break
                    # If it's RTSP/Webcam, allow short sleep and retry
                    time.sleep(0.1)
                    continue

                # Run detection & visualization pipeline
                processed_frame = processor.process_frame(frame, conf_threshold=options.get("conf_threshold", 0.25))
                
                # Encode frame to JPEG
                success, jpeg_buffer = cv2.imencode('.jpg', processed_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                
                if success:
                    with self._lock:
                        session = self.sessions.get(stream_id)
                        if session:
                            session["latest_frame"] = jpeg_buffer.tobytes()
                            session["statistics"] = analytics.get_statistics()
                            session["frame_count"] += 1
                
                # Throttle processing loop if processing was faster than video source FPS
                elapsed = time.time() - start_time
                sleep_time = frame_delay - elapsed
                if sleep_time > 0 and stream_mgr.is_file:
                    time.sleep(sleep_time)

        except Exception as e:
            self.logger.exception(f"Unhandled error in stream loop {stream_id}: {e}")
            with self._lock:
                session = self.sessions.get(stream_id)
                if session:
                    session["status"] = "failed"
                    session["error"] = str(e)
        finally:
            if stream_mgr:
                stream_mgr.stop_stream()
            
            with self._lock:
                session = self.sessions.get(stream_id)
                if session and session["status"] != "failed":
                    session["status"] = "stopped"
                    
            self.logger.info(f"Stream thread terminated for {stream_id}")

    def stop_session(self, stream_id: str) -> bool:
        """
        Stops a running stream session and releases resources.
        """
        with self._lock:
            session = self.sessions.get(stream_id)
            if not session:
                return False
            
            if session["status"] in ["running", "starting"]:
                session["status"] = "stopping"
                
        # Wait briefly for thread to exit
        thread = session.get("thread")
        if thread and thread.is_alive():
            thread.join(timeout=3.0)
            
        with self._lock:
            # Final cleanup
            if stream_id in self.sessions:
                # Remove session from dictionary to free memory
                self.sessions.pop(stream_id)
                
        self.logger.info(f"Stopped and removed stream session {stream_id}")
        return True

    def get_session_status(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves status information for a stream session.
        """
        with self._lock:
            session = self.sessions.get(stream_id)
            if not session:
                return None
            
            return {
                "stream_id": stream_id,
                "status": session["status"],
                "source": session["source"],
                "width": session["width"],
                "height": session["height"],
                "fps": session["fps"],
                "frame_count": session["frame_count"],
                "statistics": session["statistics"],
                "error": session["error"]
            }

    def get_latest_frame(self, stream_id: str) -> Optional[bytes]:
        """
        Retrieves the latest JPEG-encoded frame bytes for a session.
        """
        with self._lock:
            session = self.sessions.get(stream_id)
            if session and session["status"] == "running":
                return session["latest_frame"]
        return None

# Global session manager instance
session_manager = StreamSessionManager()
