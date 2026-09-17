import time
import cv2
import logging
from typing import Union, Optional
import numpy as np

class StreamManager:
    def __init__(self, source: Union[int, str], reconnect_interval: int = 5, max_reconnect_attempts: int = 10):
        self.logger = logging.getLogger("app.stream_manager")
        
        # If source is a digit string (e.g., "0"), convert to integer index for webcams
        if isinstance(source, str) and source.isdigit():
            self.source = int(source)
        else:
            self.source = source
            
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempts = max_reconnect_attempts
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_rtsp = isinstance(self.source, str) and (
            self.source.startswith("rtsp://") or 
            self.source.startswith("rtmp://") or 
            self.source.startswith("http://") or 
            self.source.startswith("https://")
        )
        self.is_file = isinstance(self.source, str) and not self.is_rtsp
        self.consecutive_failures = 0
        self.max_failures_before_reconnect = 15  # Reconnect after ~0.5s of failure for live streams

    def start_stream(self) -> bool:
        """
        Initializes and starts the OpenCV VideoCapture stream.
        """
        self.logger.info(f"Opening video stream source: {self.source}")
        self.stop_stream()  # Clean up any existing stream
        
        try:
            self.cap = cv2.VideoCapture(self.source)
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open video source: {self.source}")
                return False
                
            self.consecutive_failures = 0
            self.logger.info(f"Successfully started stream from source: {self.source}")
            return True
        except Exception as e:
            self.logger.exception(f"Unexpected error starting stream: {e}")
            return False

    def is_open(self) -> bool:
        """
        Checks if the VideoCapture is open.
        """
        return self.cap is not None and self.cap.isOpened()

    def read_frame(self) -> Optional[np.ndarray]:
        """
        Reads the next frame from the stream.
        If it's an RTSP stream and reading fails, attempts auto-reconnection.
        Returns:
            np.ndarray frame or None (if EOF or failure).
        """
        if not self.is_open():
            # If not open, try to start
            if not self.start_stream():
                time.sleep(self.reconnect_interval)
                return None

        try:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.consecutive_failures += 1
                self.logger.warning(f"Failed to read frame (consecutive failure {self.consecutive_failures})")
                
                # If it's an RTSP stream, try reconnecting after threshold reached
                if self.is_rtsp and self.consecutive_failures >= self.max_failures_before_reconnect:
                    self.logger.warning(f"RTSP stream connection lost. Attempting reconnection...")
                    self.reconnect()
                    
                # If video file, EOF is expected, no need to log as error/warning
                if self.is_file:
                    self.logger.info("Reached End of File (EOF) for video file.")
                    self.stop_stream()
                return None
            
            # Reset failures on successful frame read
            self.consecutive_failures = 0
            return frame
        except Exception as e:
            self.logger.error(f"Error reading frame from stream: {e}")
            self.consecutive_failures += 1
            return None

    def reconnect(self) -> bool:
        """
        Gracefully reconnects the stream.
        """
        self.logger.info(f"Reconnecting to source: {self.source}")
        self.stop_stream()
        
        for attempt in range(1, self.max_reconnect_attempts + 1):
            self.logger.info(f"Reconnection attempt {attempt}/{self.max_reconnect_attempts}...")
            if self.start_stream():
                self.logger.info("Reconnection successful.")
                return True
            time.sleep(self.reconnect_interval)
            
        self.logger.error(f"Reconnection failed after {self.max_reconnect_attempts} attempts.")
        return False

    def stop_stream(self):
        """
        Releases the OpenCV VideoCapture resource.
        """
        if self.cap is not None:
            self.logger.info(f"Releasing stream source: {self.source}")
            self.cap.release()
            self.cap = None

    def get_fps(self) -> float:
        """
        Retrieves the stream FPS. Returns a default of 30.0 if not available.
        """
        if self.is_open():
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            if fps > 0:
                return fps
        return 30.0

    def get_dimensions(self) -> tuple[int, int]:
        """
        Retrieves width and height of the stream. Returns (640, 480) as fallback.
        """
        if self.is_open():
            w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if w > 0 and h > 0:
                return w, h
        return 640, 480
