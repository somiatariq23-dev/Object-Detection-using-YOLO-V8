import logging
from typing import Dict, List, Set, Union
import numpy as np

class AnalyticsManager:
    # COCO Class mapping for target categories
    CLASS_MAP = {
        0: "person",
        1: "bike",       # bicycle
        2: "car",
        3: "bike",       # motorcycle
        5: "bus",
        7: "truck"
    }

    def __init__(self):
        self.logger = logging.getLogger("app.analytics_manager")
        
        # Cumulative unique tracking IDs seen per class
        self.tracked_ids: Dict[str, Set[int]] = {
            "person": set(),
            "car": set(),
            "bus": set(),
            "truck": set(),
            "bike": set()
        }
        
        # Current frame counts
        self.current_counts: Dict[str, int] = {
            "person": 0,
            "car": 0,
            "bus": 0,
            "truck": 0,
            "bike": 0
        }
        
        # Cumulative total counts (fallback when tracker is disabled)
        # Keeps peak count seen in a single frame as a baseline fallback
        self.peak_counts: Dict[str, int] = {
            "person": 0,
            "car": 0,
            "bus": 0,
            "truck": 0,
            "bike": 0
        }

    def reset(self):
        """
        Resets all counters.
        """
        for category in self.tracked_ids:
            self.tracked_ids[category].clear()
            self.current_counts[category] = 0
            self.peak_counts[category] = 0
        self.logger.info("Analytics counts reset.")

    def update_counts(self, class_ids: np.ndarray, track_ids: np.ndarray = None):
        """
        Updates current frame counts and cumulative unique tracked counts.
        class_ids: numpy array of detected class IDs
        track_ids: numpy array of corresponding track IDs (optional)
        """
        # Reset current frame counts
        for category in self.current_counts:
            self.current_counts[category] = 0
            
        if len(class_ids) == 0:
            return

        for idx, cid in enumerate(class_ids):
            category = self.CLASS_MAP.get(int(cid))
            if category:
                # Increment current frame count
                self.current_counts[category] += 1
                
                # Update peak counts
                if self.current_counts[category] > self.peak_counts[category]:
                    self.peak_counts[category] = self.current_counts[category]
                
                # If tracker is active, track unique object IDs to calculate true cumulative count
                if track_ids is not None and idx < len(track_ids):
                    tid = int(track_ids[idx])
                    self.tracked_ids[category].add(tid)

    def get_statistics(self) -> Dict[str, Union[Dict[str, int], Dict[str, int]]]:
        """
        Compiles and returns current metrics.
        """
        cumulative = {}
        for category, ids in self.tracked_ids.items():
            # If tracking was used, cumulative counts = size of unique set of track IDs.
            # If tracking wasn't used, fallback to the peak count recorded.
            cumulative[category] = len(ids) if len(ids) > 0 else self.peak_counts[category]

        return {
            "current": self.current_counts.copy(),
            "cumulative": cumulative
        }
