import os
import sys
import cv2

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# Attempt to import DeepSORT
try:
    from deep_sort_realtime.deepsort_tracker import DeepSort
    DEEPSORT_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: deep_sort_realtime not available. Install it with: pip install deep-sort-realtime")
    DEEPSORT_AVAILABLE = False


class MultiObjectTracker:
    def __init__(self, max_age=30, n_init=3):
        """
        Initialize multi-object tracker.
        If DeepSORT is available, use it; otherwise, fallback to a simple IoU-based tracker.
        """
        if DEEPSORT_AVAILABLE:
            self.tracker = DeepSort(max_age=max_age, n_init=n_init)
            self.use_deepsort = True
        else:
            self.use_deepsort = False
            self.next_id = 1
            self.tracks = {}
            self.max_age = max_age
            print("🟡 Using simple IoU-based tracking fallback (DeepSORT not available).")

    def update(self, frame, detections):
        """
        Update tracking for a given frame and YOLO detections.
        detections format: [(bbox, conf, cls), ...]
        bbox = (x1, y1, x2, y2)
        """
        if self.use_deepsort:
            return self._update_deepsort(frame, detections)
        else:
            return self._update_simple(frame, detections)

    # -------------------- DeepSORT Tracking -------------------- #
    def _update_deepsort(self, frame, detections):
        """
        Update using DeepSORT while preserving YOLO boxes for display.
        """
        try:
            # Convert detections to DeepSORT input format
            deepsort_inputs = []
            for det in detections:
                bbox, conf, cls = det
                x1, y1, x2, y2 = bbox
                w = x2 - x1
                h = y2 - y1
                deepsort_inputs.append(([x1, y1, w, h], conf, cls))

            tracks = self.tracker.update_tracks(deepsort_inputs, frame=frame)
            tracked_objects = []

            for track in tracks:
                if not track.is_confirmed():
                    continue

                track_id = track.track_id
                ltrb = track.to_ltrb()  # [x1, y1, x2, y2]
                x1, y1, x2, y2 = map(int, ltrb)

                tracked_objects.append({
                    "id": track_id,
                    "bbox": (x1, y1, x2, y2)
                })

            return tracked_objects

        except Exception as e:
            print(f"❌ Error in DeepSORT tracking: {e}")
            return []

    # -------------------- Simple Fallback Tracker -------------------- #
    def _update_simple(self, frame, detections):
        """
        Simple IoU-based tracking fallback if DeepSORT is not available.
        """
        tracked_objects = []
        current_detections = [(det[0], det[1]) for det in detections]  # (bbox, conf)
        matched_tracks = []

        for bbox, conf in current_detections:
            best_match = None
            best_overlap = 0

            for track_id, track_data in list(self.tracks.items()):
                if track_data['age'] > self.max_age:
                    continue

                overlap = self._calculate_overlap(bbox, track_data['bbox'])
                if overlap > best_overlap and overlap > 0.3:  # IoU threshold
                    best_overlap = overlap
                    best_match = track_id

            if best_match:
                # Update existing track
                self.tracks[best_match]['bbox'] = bbox
                self.tracks[best_match]['age'] = 0
                matched_tracks.append(best_match)

                tracked_objects.append({
                    "id": best_match,
                    "bbox": tuple(map(int, bbox))
                })
            else:
                # Create new track
                track_id = self.next_id
                self.next_id += 1
                self.tracks[track_id] = {'bbox': bbox, 'age': 0}
                matched_tracks.append(track_id)

                tracked_objects.append({
                    "id": track_id,
                    "bbox": tuple(map(int, bbox))
                })

        # Increment age for unmatched tracks and remove expired ones
        for track_id in list(self.tracks.keys()):
            if track_id not in matched_tracks:
                self.tracks[track_id]['age'] += 1
                if self.tracks[track_id]['age'] > self.max_age:
                    del self.tracks[track_id]

        return tracked_objects

    @staticmethod
    def _calculate_overlap(box1, box2):
        """
        Compute Intersection-over-Union (IoU) between two bounding boxes.
        """
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2

        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)

        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0

        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0
