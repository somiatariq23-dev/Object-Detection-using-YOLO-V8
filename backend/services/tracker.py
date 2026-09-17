import numpy as np
from scipy.optimize import linear_sum_assignment
import logging

logger = logging.getLogger("app.tracker")

def iou_batch(bb_test, bb_gt):
    """
    Computes IoU between two sets of bounding boxes.
    bb_test: [N, 4] (predictions)
    bb_gt: [M, 4] (detections)
    Returns [N, M] IoU matrix.
    """
    bb_gt = np.expand_dims(bb_gt, 0)
    bb_test = np.expand_dims(bb_test, 1)

    xx1 = np.maximum(bb_test[..., 0], bb_gt[..., 0])
    yy1 = np.maximum(bb_test[..., 1], bb_gt[..., 1])
    xx2 = np.minimum(bb_test[..., 2], bb_gt[..., 2])
    yy2 = np.minimum(bb_test[..., 3], bb_gt[..., 3])
    
    w = np.maximum(0., xx2 - xx1)
    h = np.maximum(0., yy2 - yy1)
    
    wh = w * h
    o = wh / (
        (bb_test[..., 2] - bb_test[..., 0]) * (bb_test[..., 3] - bb_test[..., 1])
        + (bb_gt[..., 2] - bb_gt[..., 0]) * (bb_gt[..., 3] - bb_gt[..., 1])
        - wh
    )
    return o

class KalmanBoxTracker:
    count = 0
    
    def __init__(self, bbox):
        """
        Initializes a tracker using initial bounding box [x1, y1, x2, y2].
        """
        # State: [x, y, s, r, vx, vy, vs]
        # x, y: center coordinates
        # s: scale (area)
        # r: aspect ratio
        # vx, vy, vs: velocities
        self.kf_init(bbox)
        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0
        self.last_bbox = bbox

    def kf_init(self, bbox):
        # Convert [x1, y1, x2, y2] to [x, y, s, r]
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = bbox[0] + w / 2.0
        y = bbox[1] + h / 2.0
        s = w * h
        r = w / float(h) if h > 0 else 0
        
        # State Vector
        self.x = np.array([[x], [y], [s], [r], [0.0], [0.0], [0.0]], dtype=np.float32)
        
        # State Transition Matrix
        self.F = np.array([
            [1, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 1]
        ], dtype=np.float32)
        
        # Measurement Matrix (we only measure [x, y, s, r])
        self.H = np.array([
            [1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0]
        ], dtype=np.float32)
        
        # Covariance Matrices
        self.P = np.eye(7, dtype=np.float32) * 10.0
        self.P[4:, 4:] *= 1000.0  # high uncertainty for initial velocity
        
        self.Q = np.eye(7, dtype=np.float32)
        self.Q[4:, 4:] *= 0.01
        
        self.R = np.eye(4, dtype=np.float32)
        self.R[2, 2] *= 10.0
        self.R[3, 3] *= 10.0

    def predict(self):
        """
        Advances the state vector and returns the predicted bounding box estimate.
        """
        if (self.x[2] + self.x[6]) <= 0:
            self.x[6] *= 0.0
            
        self.x = np.dot(self.F, self.x)
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q
        
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        
        self.history.append(self.get_state())
        return self.history[-1]

    def update(self, bbox):
        """
        Updates the state vector with observed bbox.
        """
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1
        self.last_bbox = bbox
        
        # Convert [x1, y1, x2, y2] to measurement vector z
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = bbox[0] + w / 2.0
        y = bbox[1] + h / 2.0
        s = w * h
        r = w / float(h) if h > 0 else 0
        z = np.array([[x], [y], [s], [r]], dtype=np.float32)
        
        # Kalman Gain
        S = np.dot(np.dot(self.H, self.P), self.H.T) + self.R
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))
        
        # Update State and Covariance
        y_err = z - np.dot(self.H, self.x)
        self.x = self.x + np.dot(K, y_err)
        self.P = self.P - np.dot(np.dot(K, self.H), self.P)

    def get_state(self):
        """
        Returns the current bounding box estimate [x1, y1, x2, y2].
        """
        # Convert [x, y, s, r] to [x1, y1, x2, y2]
        x, y, s, r = self.x[0, 0], self.x[1, 0], self.x[2, 0], self.x[3, 0]
        w = np.sqrt(s * r)
        h = s / w if w > 0 else 0
        
        x1 = x - w / 2.0
        y1 = y - h / 2.0
        x2 = x + w / 2.0
        y2 = y + h / 2.0
        return np.array([x1, y1, x2, y2], dtype=np.float32)


class Tracker:
    def __init__(self, max_age: int = 15, min_hits: int = 3, iou_threshold: float = 0.3):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.trackers = []
        self.frame_count = 0

    def update(self, dets: np.ndarray, class_ids: np.ndarray = None) -> np.ndarray:
        """
        Params:
          dets - a numpy array of detections in the format [[x1,y1,x2,y2,score], [x1,y1,x2,y2,score],...]
          class_ids - a numpy array of class labels for each detection
        Requires: this method must be called once for each frame even with empty detections.
        Returns a similar array where the last column is the object ID, class ID, and confidence:
          [[x1,y1,x2,y2,track_id,class_id,score],...]
        """
        self.frame_count += 1
        
        # If class_ids is not passed, default to all zeros
        if class_ids is None:
            class_ids = np.zeros(len(dets), dtype=int)
            
        # Get predicted locations from existing trackers
        trks = np.zeros((len(self.trackers), 5))
        to_del = []
        ret = []
        
        for t, trk in enumerate(trks):
            pos = self.trackers[t].predict()
            trk[:] = [pos[0], pos[1], pos[2], pos[3], 0]
            if np.any(np.isnan(pos)):
                to_del.append(t)
                
        trks = np.delete(trks, to_del, axis=0)
        for index in sorted(to_del, reverse=True):
            self.trackers.pop(index)
            
        # If no detections, just update tracks and return empty
        if len(dets) == 0:
            # We still need to cleanup expired tracks
            self.trackers = [t for t in self.trackers if t.time_since_update < self.max_age]
            return np.empty((0, 7))

        # Separate bbox coordinates and confidence scores
        dets_box = dets[:, :4]
        dets_score = dets[:, 4] if dets.shape[1] > 4 else np.ones(len(dets))

        matched, unmatched_dets, unmatched_trks = self.associate_detections_to_trackers(
            dets_box, trks[:, :4], self.iou_threshold
        )

        # Update matched trackers with assigned detections
        for m in matched:
            self.trackers[m[1]].update(dets_box[m[0]])
            # Attach metadata: class_id and score
            self.trackers[m[1]].class_id = class_ids[m[0]]
            self.trackers[m[1]].score = dets_score[m[0]]

        # Create and initialize new trackers for unmatched detections
        for i in unmatched_dets:
            trk = KalmanBoxTracker(dets_box[i])
            trk.class_id = class_ids[i]
            trk.score = dets_score[i]
            self.trackers.append(trk)
            
        # Generate outputs and filter out dead trackers
        i = len(self.trackers)
        for trk in reversed(self.trackers):
            d = trk.get_state()
            if (trk.time_since_update < 1) and (trk.hit_streak >= self.min_hits or self.frame_count <= self.min_hits):
                # Format: [x1, y1, x2, y2, track_id, class_id, score]
                ret.append(np.concatenate((d, [trk.id, trk.class_id, trk.score])))
            i -= 1
            # Remove dead tracks
            if trk.time_since_update > self.max_age:
                self.trackers.remove(trk)
                
        if len(ret) > 0:
            return np.stack(ret)
        return np.empty((0, 7))

    def associate_detections_to_trackers(self, detections, trackers, iou_threshold):
        """
        Assigns detections to tracked object (both represent bounding boxes).
        Returns:
            matched: list of match pairs (detection_idx, tracker_idx)
            unmatched_detections: indices of detections not matched
            unmatched_trackers: indices of trackers not matched
        """
        if len(trackers) == 0:
            return np.empty((0, 2), dtype=int), np.arange(len(detections)), np.empty((0,), dtype=int)

        iou_matrix = iou_batch(detections, trackers)

        if min(iou_matrix.shape) > 0:
            a = (iou_matrix > iou_threshold).astype(np.int32)
            if a.sum(1).max() == 1 and a.sum(0).max() == 1:
                matched_indices = np.stack(np.where(a), axis=1)
            else:
                # Solve using Hungarian Algorithm (cost = -IoU)
                x, y = linear_sum_assignment(-iou_matrix)
                matched_indices = np.stack((x, y), axis=1)
        else:
            matched_indices = np.empty((0, 2), dtype=int)

        unmatched_detections = []
        for d, det in enumerate(detections):
            if d not in matched_indices[:, 0]:
                unmatched_detections.append(d)
                
        unmatched_trackers = []
        for t, trk in enumerate(trackers):
            if t not in matched_indices[:, 1]:
                unmatched_trackers.append(t)

        # Filter out matches with low IoU
        matches = []
        for m in matched_indices:
            if iou_matrix[m[0], m[1]] < iou_threshold:
                unmatched_detections.append(m[0])
                unmatched_trackers.append(m[1])
            else:
                matches.append(m.reshape(1, 2))
                
        if len(matches) == 0:
            matches = np.empty((0, 2), dtype=int)
        else:
            matches = np.concatenate(matches, axis=0)

        return matches, np.array(unmatched_detections), np.array(unmatched_trackers)
