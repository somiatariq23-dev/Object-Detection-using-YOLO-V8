import cv2
import os
import logging
from pathlib import Path
from typing import Optional
import numpy as np

class VideoWriterService:
    def __init__(self):
        self.logger = logging.getLogger("app.video_writer")
        self.writer: Optional[cv2.VideoWriter] = None
        self.output_path: Optional[str] = None

    def initialize_writer(self, output_path: str, width: int, height: int, fps: float) -> bool:
        """
        Initializes the cv2.VideoWriter with MP4 codec.
        Automatically creates target directories.
        """
        self.release()  # Clean up any active writer
        
        self.output_path = output_path
        out_file = Path(output_path)
        
        # Auto-create output directory
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Use mp4v codec
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        
        try:
            self.writer = cv2.VideoWriter(
                str(out_file),
                fourcc,
                fps,
                (width, height)
            )
            
            if not self.writer.isOpened():
                self.logger.error(f"Failed to open video writer for path: {output_path}")
                self.writer = None
                return False
                
            self.logger.info(f"Video writer initialized successfully at: {output_path} ({width}x{height} @ {fps} FPS)")
            return True
        except Exception as e:
            self.logger.exception(f"Error initializing video writer: {e}")
            self.writer = None
            return False

    def write_frame(self, frame: np.ndarray):
        """
        Writes a single frame.
        """
        if self.writer is None:
            self.logger.warning("Writer is not initialized. Frame not written.")
            return
            
        try:
            self.writer.write(frame)
        except Exception as e:
            self.logger.error(f"Failed to write frame: {e}")

    def release(self):
        """
        Releases the VideoWriter resource.
        """
        if self.writer is not None:
            self.logger.info(f"Releasing video writer for: {self.output_path}")
            self.writer.release()
            self.writer = None
            self.output_path = None

