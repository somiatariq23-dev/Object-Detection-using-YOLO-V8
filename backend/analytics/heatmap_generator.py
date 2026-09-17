import cv2
import numpy as np
from typing import List, Tuple, Optional

class HeatmapGenerator:
    def __init__(self, width: int = None, height: int = None, decay: float = 0.999, radius: int = 25, intensity: float = 5.0):
        """
        decay: multiplier applied to the heatmap each frame to fade old tracks.
               If 1.0, heatmap accumulates indefinitely.
        radius: the radius of influence of a single detection on the heatmap.
        intensity: amount of weight added per detection.
        """
        self.width = width
        self.height = height
        self.decay = decay
        self.radius = radius
        self.intensity = intensity
        
        self.heatmap: Optional[np.ndarray] = None

    def _init_heatmap(self, width: int, height: int):
        self.width = width
        self.height = height
        self.heatmap = np.zeros((height, width), dtype=np.float32)

    def update_heatmap(self, boxes: np.ndarray, frame_shape: Tuple[int, int, int]):
        """
        Accumulates object centers into the heatmap grid.
        boxes: Nx4 array or list of [x1, y1, x2, y2]
        frame_shape: (height, width, channels) format of the current frame
        """
        h, w = frame_shape[0], frame_shape[1]
        if self.heatmap is None or self.width != w or self.height != h:
            self._init_heatmap(w, h)
            
        # Apply decay to fade historical detections
        self.heatmap *= self.decay
        
        if len(boxes) == 0:
            return

        # Create temporary accumulation frame for current detections
        current_accumulation = np.zeros((h, w), dtype=np.float32)
        
        for box in boxes:
            x1, y1, x2, y2 = box[:4]
            # Find center point of bounding box
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            
            # Bound coordinates
            if 0 <= cx < w and 0 <= cy < h:
                # Draw a soft radial gradient circle on the current frame
                # To do this efficiently, we draw a filled circle using OpenCV
                cv2.circle(current_accumulation, (cx, cy), self.radius, float(self.intensity), -1)
                
        # Blur the current detections to make the heatmap smooth and continuous
        if np.any(current_accumulation > 0):
            # Apply Gaussian Blur to create a smooth drop-off
            kernel_size = self.radius * 2 + 1
            # Must be odd
            if kernel_size % 2 == 0:
                kernel_size += 1
            blurred = cv2.GaussianBlur(current_accumulation, (kernel_size, kernel_size), 0)
            self.heatmap += blurred

    def render_heatmap(self, base_frame: np.ndarray, alpha: float = 0.5) -> np.ndarray:
        """
        Overlays the cumulative heatmap onto the base_frame.
        alpha: visibility weight of the heatmap (0.0 to 1.0)
        """
        if self.heatmap is None:
            return base_frame.copy()
            
        h, w = base_frame.shape[0], base_frame.shape[1]
        
        # Avoid dividing by zero if heatmap is completely black
        max_val = np.max(self.heatmap)
        if max_val <= 0:
            return base_frame.copy()
            
        # Normalize heatmap to [0, 255] and convert to uint8
        normalized = np.clip((self.heatmap / max_val) * 255.0, 0, 255).astype(np.uint8)
        
        # Apply JET Colormap
        heatmap_color = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
        
        # Blend heatmap with base frame only where density exists
        # This keeps the background clean (without a uniform blue tint)
        mask = normalized > 5
        
        output_frame = base_frame.copy()
        if np.any(mask):
            # Apply blend
            blended = cv2.addWeighted(base_frame, 1.0 - alpha, heatmap_color, alpha, 0)
            output_frame[mask] = blended[mask]
            
        return output_frame

    def reset(self):
        """
        Clears the current heatmap state.
        """
        if self.heatmap is not None:
            self.heatmap.fill(0)
