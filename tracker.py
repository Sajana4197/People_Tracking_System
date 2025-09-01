try:
    from deep_sort_realtime.deepsort_tracker import DeepSort
    DEEPSORT_AVAILABLE = True
except ImportError:
    print("Warning: deep_sort_realtime not available. Install with: pip install deep-sort-realtime")
    DEEPSORT_AVAILABLE = False
    
import cv2

class MultiObjectTracker:
    def __init__(self, max_age=30, n_init=3):
        if DEEPSORT_AVAILABLE:
            self.tracker = DeepSort(max_age=max_age, n_init=n_init)
            self.use_deepsort = True
        else:
            # Fallback to simple tracking
            self.use_deepsort = False
            self.next_id = 1
            self.tracks = {}
            self.max_age = max_age
            print("Using simple tracking fallback")

    def update(self, frame, detections):
        if self.use_deepsort:
            return self._update_deepsort(frame, detections)
        else:
            return self._update_simple(frame, detections)

    def _update_deepsort(self, frame, detections):
        """Update using DeepSORT"""
        try:
            tracks = self.tracker.update_tracks(detections, frame=frame)
            tracked_objects = []
            
            for track in tracks:
                if not track.is_confirmed():
                    continue

                # Get tight bounding box from DeepSORT
                l, t, r, b = track.to_ltrb()
                
                # Ensure valid coordinates
                l, t, r, b = max(0, int(l)), max(0, int(t)), int(r), int(b)
                
                if r > l and b > t:  # Valid box
                    tracked_objects.append({
                        "id": track.track_id,
                        "bbox": (l, t, r, b)
                    })
                    
            return tracked_objects
            
        except Exception as e:
            print(f"Error in DeepSORT tracking: {e}")
            return []

    def _update_simple(self, frame, detections):
        """Simple tracking fallback using overlap-based matching"""
        tracked_objects = []
        current_detections = [(det[0], det[1]) for det in detections]  # (bbox, conf)
        
        # Simple overlap-based tracking
        matched_tracks = []
        for bbox, conf in current_detections:
            x1, y1, x2, y2 = bbox
            best_match = None
            best_overlap = 0
            
            # Find best matching existing track
            for track_id, track_data in self.tracks.items():
                if track_data['age'] > self.max_age:
                    continue
                    
                tx1, ty1, tx2, ty2 = track_data['bbox']
                overlap = self._calculate_overlap(bbox, track_data['bbox'])
                
                if overlap > best_overlap and overlap > 0.3:  # Minimum overlap threshold
                    best_overlap = overlap
                    best_match = track_id
            
            if best_match:
                # Update existing track
                self.tracks[best_match]['bbox'] = bbox
                self.tracks[best_match]['age'] = 0
                matched_tracks.append(best_match)
                tracked_objects.append({
                    "id": best_match,
                    "bbox": bbox
                })
            else:
                # Create new track
                track_id = self.next_id
                self.next_id += 1
                self.tracks[track_id] = {
                    'bbox': bbox,
                    'age': 0
                }
                matched_tracks.append(track_id)
                tracked_objects.append({
                    "id": track_id,
                    "bbox": bbox
                })
        
        # Age unmatched tracks
        for track_id in list(self.tracks.keys()):
            if track_id not in matched_tracks:
                self.tracks[track_id]['age'] += 1
                if self.tracks[track_id]['age'] > self.max_age:
                    del self.tracks[track_id]
        
        return tracked_objects

    def _calculate_overlap(self, box1, box2):
        """Calculate IoU (Intersection over Union) between two boxes"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # Calculate intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i <= x1_i or y2_i <= y1_i:
            return 0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0