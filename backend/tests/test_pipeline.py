import os
import sys
import numpy as np
from pathlib import Path

# Add backend directory to Python path if running script directly
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.core.device_manager import device_manager
from backend.services.yolo_engine import YOLOEngine
from backend.services.tracker import Tracker
from backend.analytics.analytics_manager import AnalyticsManager
from backend.analytics.heatmap_generator import HeatmapGenerator
from backend.services.video_processor import VideoProcessor

def test_pipeline():
    print("=== STARTING PIPELINE INTEGRATION TEST ===")
    
    # 1. Test Device Manager
    print("\n--- 1. Testing Device Manager ---")
    device_manager.print_device_info()
    device = device_manager.get_device()
    assert device in ["cuda", "cpu"], f"Invalid device: {device}"
    print(f"Device Manager check passed: Running on {device}")
    
    # 2. Test YOLO Engine
    print("\n--- 2. Testing YOLO Engine ---")
    yolo = YOLOEngine()
    print("YOLO Engine initialized successfully.")
    
    # 3. Test Components
    print("\n--- 3. Testing Component Modules ---")
    tracker = Tracker()
    analytics = AnalyticsManager()
    
    # Create mock frame (640x480 RGB image)
    width, height = 640, 480
    mock_frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Draw some mock shapes to simulate objects
    cv2_available = True
    try:
        import cv2
        # Draw a white rectangle in the center
        cv2.rectangle(mock_frame, (200, 150), (440, 330), (255, 255, 255), -1)
        print("Draw mock shapes using OpenCV.")
    except ImportError:
        cv2_available = False
        print("OpenCV not installed in test environment, using empty frame.")
        
    heatmap = HeatmapGenerator(width=width, height=height)
    print("Tracker, Analytics, and Heatmap modules initialized.")
    
    # 4. Test Video Processor Pipeline
    print("\n--- 4. Testing Video Processor Pipeline ---")
    processor = VideoProcessor(
        yolo_engine=yolo,
        tracker=tracker,
        analytics_manager=analytics,
        heatmap_generator=heatmap,
        draw_tracking=True,
        draw_heatmap=True,
        draw_hud=True
    )
    
    processed_frame = processor.process_frame(mock_frame, conf_threshold=0.1)
    
    # Validate processed frame dimensions
    assert processed_frame.shape == mock_frame.shape, "Annotated frame shape mismatch!"
    print("Frame processed successfully through pipeline.")
    
    # Check stats
    stats = analytics.get_statistics()
    print(f"Extraction Statistics: {stats}")
    assert "current" in stats
    assert "cumulative" in stats
    
    print("\n=== INTEGRATION TEST PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    test_pipeline()
