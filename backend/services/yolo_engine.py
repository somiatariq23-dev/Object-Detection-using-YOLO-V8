import os
import logging
from typing import List, Tuple, Union
import numpy as np
from ultralytics import YOLO

from backend.config.settings import settings
from backend.core.device_manager import device_manager

class YOLOEngine:
    def __init__(self, model_name: str = None):
        self.logger = logging.getLogger("app.yolo_engine")
        self.device = device_manager.get_device()
        self.model_name = model_name or settings.MODEL_NAME
        
        # Determine paths
        self.weights_dir = settings.WEIGHTS_DIR
        self.weights_dir.mkdir(parents=True, exist_ok=True)
        self.model_path = self.weights_dir / self.model_name
        
        self.model = None
        self.load_model()

    def load_model(self):
        """
        Loads the YOLOv8 model weights onto the detected system device.
        """
        self.logger.info(f"Loading YOLO model '{self.model_name}' on device '{self.device}'...")
        try:
            # If the weights do not exist locally, Ultralytics downloads them to the current working dir by default.
            # We enforce saving them under weights/ to keep the structure clean.
            if not self.model_path.exists():
                self.logger.info(f"Weights not found at {self.model_path}. Model will download automatically to the target folder.")
                
            # YOLO constructor
            self.model = YOLO(str(self.model_path))
            # Move model to target device
            self.model.to(self.device)
            self.logger.info("YOLO model loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load YOLO model: {e}")
            raise e

    def predict(self, frame: np.ndarray, conf_threshold: float = 0.25) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Runs object detection on a single frame.
        Returns:
            boxes: Nx4 array of bounding boxes [x1, y1, x2, y2]
            class_ids: N-dim array of class integer IDs
            confidences: N-dim array of floats
        """
        if self.model is None:
            raise RuntimeError("Model is not loaded. Call load_model() first.")
        
        # Run prediction
        # stream=True can optimize memory for videos, but since we receive single frames here we run standard predict
        results = self.model.predict(
            source=frame,
            device=self.device,
            conf=conf_threshold,
            verbose=False
        )
        
        if not results:
            return np.empty((0, 4)), np.empty((0,)), np.empty((0,))
            
        result = results[0]
        boxes = result.boxes.xyxy.cpu().numpy()  # bounding box coordinates
        class_ids = result.boxes.cls.cpu().numpy().astype(int)  # class IDs
        confidences = result.boxes.conf.cpu().numpy()  # confidence scores
        
        return boxes, class_ids, confidences

    def batch_predict(self, frames: List[np.ndarray], conf_threshold: float = 0.25) -> List[Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        """
        Runs batch prediction on a list of frames to optimize execution speed.
        Returns:
            List of tuples, each containing (boxes, class_ids, confidences) for the corresponding frame.
        """
        if self.model is None:
            raise RuntimeError("Model is not loaded. Call load_model() first.")
            
        if not frames:
            return []
            
        # Run batch prediction
        results = self.model.predict(
            source=frames,
            device=self.device,
            conf=conf_threshold,
            verbose=False
        )
        
        output = []
        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()
            class_ids = result.boxes.cls.cpu().numpy().astype(int)
            confidences = result.boxes.conf.cpu().numpy()
            output.append((boxes, class_ids, confidences))
            
        return output
