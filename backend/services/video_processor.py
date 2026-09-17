import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional

from backend.services.yolo_engine import YOLOEngine
from backend.services.tracker import Tracker
from backend.analytics.analytics_manager import AnalyticsManager
from backend.analytics.heatmap_generator import HeatmapGenerator

class VideoProcessor:
    # Color palette (BGR format)
    COLORS = {
        "person": (46, 204, 113),  # Emerald Green
        "car": (52, 152, 219),    # Peter River Blue
        "bus": (241, 196, 15),    # Sun Flower Yellow
        "truck": (230, 126, 34),  # Carrot Orange
        "bike": (155, 89, 182),   # Amethyst Purple
        "default": (149, 165, 166) # Concrete Grey
    }

    def __init__(
        self,
        yolo_engine: YOLOEngine,
        tracker: Optional[Tracker] = None,
        analytics_manager: Optional[AnalyticsManager] = None,
        heatmap_generator: Optional[HeatmapGenerator] = None,
        draw_tracking: bool = True,
        draw_heatmap: bool = False,
        draw_hud: bool = True
    ):
        self.logger = logging.getLogger("app.video_processor")
        self.yolo = yolo_engine
        self.tracker = tracker or Tracker()
        self.analytics = analytics_manager or AnalyticsManager()
        self.heatmap = heatmap_generator or HeatmapGenerator()
        
        self.draw_tracking = draw_tracking
        self.draw_heatmap = draw_heatmap
        self.draw_hud = draw_hud

    def process_frame(self, frame: np.ndarray, conf_threshold: float = 0.25) -> np.ndarray:
        """
        Main execution step.
        1. Predict boxes, classes, confidences.
        2. Filter target classes.
        3. Update tracker.
        4. Update heatmap.
        5. Update analytics counters.
        6. Render overlays.
        """
        # Copy frame to avoid modifying original
        annotated_frame = frame.copy()
        h, w, c = annotated_frame.shape

        # 1. Run inference
        boxes, class_ids, confidences = self.yolo.predict(frame, conf_threshold=conf_threshold)

        # Filter detections for our target classes (person, bike, car, bus, truck)
        target_indices = []
        for i, cid in enumerate(class_ids):
            if int(cid) in self.analytics.CLASS_MAP:
                target_indices.append(i)
                
        if len(target_indices) > 0:
            boxes = boxes[target_indices]
            class_ids = class_ids[target_indices]
            confidences = confidences[target_indices]
        else:
            boxes = np.empty((0, 4))
            class_ids = np.empty((0,), dtype=int)
            confidences = np.empty((0,))

        # 2. Update tracking
        track_ids = None
        tracked_boxes = np.empty((0, 7))
        
        if self.draw_tracking and len(boxes) > 0:
            # Format detections for tracker: [[x1, y1, x2, y2, score], ...]
            dets_with_score = np.hstack((boxes, confidences.reshape(-1, 1)))
            tracked_boxes = self.tracker.update(dets_with_score, class_ids=class_ids)
            
            if len(tracked_boxes) > 0:
                # Extract tracked coordinates and labels
                boxes = tracked_boxes[:, :4]
                track_ids = tracked_boxes[:, 4].astype(int)
                class_ids = tracked_boxes[:, 5].astype(int)
                confidences = tracked_boxes[:, 6]
        elif self.draw_tracking:
            # Even if no detections, call tracker update to decay old track ages
            self.tracker.update(np.empty((0, 5)))

        # 3. Update heatmap
        if self.draw_heatmap:
            self.heatmap.update_heatmap(boxes, annotated_frame.shape)

        # 4. Update analytics counters
        self.analytics.update_counts(class_ids, track_ids)

        # 5. Render overlays
        # Render Heatmap first (so that boxes and HUD are drawn on top of it)
        if self.draw_heatmap:
            annotated_frame = self.heatmap.render_heatmap(annotated_frame)

        # Render Bounding boxes
        annotated_frame = self.annotate_frame(annotated_frame, boxes, class_ids, confidences, track_ids)

        # Render HUD (Heads-Up Display Dashboard overlay)
        if self.draw_hud:
            annotated_frame = self.draw_hud_panel(annotated_frame)

        return annotated_frame

    def annotate_frame(
        self,
        frame: np.ndarray,
        boxes: np.ndarray,
        class_ids: np.ndarray,
        confidences: np.ndarray,
        track_ids: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Draws bounding boxes, classes, and track labels.
        """
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box[:4])
            cid = int(class_ids[i])
            conf = float(confidences[i])
            
            # Map class name
            class_name = self.analytics.CLASS_MAP.get(cid, "unknown")
            color = self.COLORS.get(class_name, self.COLORS["default"])
            
            # Determine label text
            if track_ids is not None and i < len(track_ids):
                tid = int(track_ids[i])
                label = f"ID:{tid} | {class_name} {conf:.0%}"
            else:
                label = f"{class_name} {conf:.0%}"
                
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw text label background
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            y1_label = max(y1, h + 10)
            cv2.rectangle(frame, (x1, y1_label - h - 6), (x1 + w + 10, y1_label), color, -1)
            
            # Draw text label
            cv2.putText(
                frame,
                label,
                (x1 + 5, y1_label - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                lineType=cv2.LINE_AA
            )
            
        return frame

    def draw_hud_panel(self, frame: np.ndarray) -> np.ndarray:
        """
        Draws a semi-transparent HUD showing active counts.
        """
        stats = self.analytics.get_statistics()
        current = stats["current"]
        cumulative = stats["cumulative"]
        
        # Coordinates for HUD panel
        px1, py1, px2, py2 = 10, 10, 240, 170
        
        # Ensure HUD fits on screen
        h, w = frame.shape[:2]
        if w < px2 or h < py2:
            return frame
            
        overlay = frame.copy()
        
        # Semi-transparent dark background
        cv2.rectangle(overlay, (px1, py1), (px2, py2), (15, 15, 15), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Draw Border
        cv2.rectangle(frame, (px1, py1), (px2, py2), (80, 80, 80), 1)
        
        # Title text
        cv2.putText(
            frame,
            "VIDEO ANALYTICS HUD",
            (px1 + 10, py1 + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (200, 200, 200),
            1,
            lineType=cv2.LINE_AA
        )
        
        # Draw counts for each category
        y_offset = py1 + 45
        for idx, (category, color) in enumerate(self.COLORS.items()):
            if category == "default":
                continue
                
            curr_val = current.get(category, 0)
            cum_val = cumulative.get(category, 0)
            
            label = f"{category.upper()}:"
            count_str = f"Live:{curr_val} | Tot:{cum_val}"
            
            # Colored circle indicator
            cv2.circle(frame, (px1 + 15, y_offset - 4), 4, color, -1)
            
            # Category label
            cv2.putText(
                frame,
                label,
                (px1 + 25, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (240, 240, 240),
                1,
                lineType=cv2.LINE_AA
            )
            
            # Count values
            cv2.putText(
                frame,
                count_str,
                (px1 + 105, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (200, 200, 200),
                1,
                lineType=cv2.LINE_AA
            )
            
            y_offset += 22
            
        return frame
