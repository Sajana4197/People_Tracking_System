import cv2
import numpy as np
from ultralytics import YOLO
from collections import OrderedDict
import math
import time

class ImprovedTracker:
    """
    Enhanced multi-object tracker with better ID consistency
    """
    def __init__(self, max_disappeared=60, max_distance=150):
        self.next_object_id = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.max_disappeared = max_disappeared  # Increased patience
        self.max_distance = max_distance        # Increased tolerance
        
        # Enhanced tracking features
        self.object_history = OrderedDict()     # Store position history
        self.object_velocities = OrderedDict()  # Store velocity vectors
        self.object_sizes = OrderedDict()       # Store bounding box sizes
        
    def register(self, centroid, bbox_size=None):
        """Register a new object with enhanced features"""
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.object_history[self.next_object_id] = [centroid]
        self.object_velocities[self.next_object_id] = (0, 0)
        self.object_sizes[self.next_object_id] = bbox_size or (0, 0)
        self.next_object_id += 1

    def deregister(self, object_id):
        """Remove an object from tracking"""
        del self.objects[object_id]
        del self.disappeared[object_id]
        del self.object_history[object_id]
        del self.object_velocities[object_id]
        del self.object_sizes[object_id]

    def predict_position(self, object_id):
        """Predict where an object should be based on velocity"""
        if object_id not in self.object_velocities:
            return self.objects[object_id]
        
        current_pos = self.objects[object_id]
        velocity = self.object_velocities[object_id]
        
        # Simple linear prediction
        predicted_x = current_pos[0] + velocity[0]
        predicted_y = current_pos[1] + velocity[1]
        
        return (int(predicted_x), int(predicted_y))

    def calculate_velocity(self, object_id, new_position):
        """Calculate velocity vector for an object"""
        if object_id in self.object_history and len(self.object_history[object_id]) > 0:
            old_pos = self.object_history[object_id][-1]
            velocity_x = new_position[0] - old_pos[0]
            velocity_y = new_position[1] - old_pos[1]
            
            # Smooth velocity using moving average
            if object_id in self.object_velocities:
                old_vel = self.object_velocities[object_id]
                velocity_x = 0.7 * old_vel[0] + 0.3 * velocity_x
                velocity_y = 0.7 * old_vel[1] + 0.3 * velocity_y
            
            return (velocity_x, velocity_y)
        return (0, 0)

    def size_similarity(self, size1, size2):
        """Calculate similarity between bounding box sizes"""
        if size1 == (0, 0) or size2 == (0, 0):
            return 1.0  # Default similarity
        
        w1, h1 = size1
        w2, h2 = size2
        
        # Calculate area ratio
        area1 = w1 * h1
        area2 = w2 * h2
        
        if area1 == 0 or area2 == 0:
            return 1.0
        
        ratio = min(area1, area2) / max(area1, area2)
        return ratio

    def enhanced_distance(self, obj_id, detection_centroid, detection_size):
        """Calculate enhanced distance considering multiple factors"""
        # Position distance
        obj_pos = self.objects[obj_id]
        predicted_pos = self.predict_position(obj_id)
        
        # Use predicted position for better tracking
        pos_distance = np.linalg.norm(
            np.array(predicted_pos) - np.array(detection_centroid)
        )
        
        # Size similarity
        obj_size = self.object_sizes.get(obj_id, (0, 0))
        size_sim = self.size_similarity(obj_size, detection_size)
        
        # Combine factors (lower is better)
        enhanced_dist = pos_distance / size_sim
        
        return enhanced_dist

    def update(self, detections_with_sizes):
        """
        Enhanced update method with size information
        detections_with_sizes: list of (centroid, bbox_size) tuples
        """
        if len(detections_with_sizes) == 0:
            # Mark all existing objects as disappeared
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects

        # Separate centroids and sizes
        input_centroids = [det[0] for det in detections_with_sizes]
        input_sizes = [det[1] if len(det) > 1 else (0, 0) for det in detections_with_sizes]

        if len(self.objects) == 0:
            # Register all detections as new objects
            for i, centroid in enumerate(input_centroids):
                self.register(centroid, input_sizes[i])
        else:
            # Get existing object data
            object_ids = list(self.objects.keys())

            # Calculate enhanced distance matrix
            distances = np.zeros((len(object_ids), len(input_centroids)))
            
            for i, obj_id in enumerate(object_ids):
                for j, (centroid, size) in enumerate(detections_with_sizes):
                    distances[i, j] = self.enhanced_distance(obj_id, centroid, size)

            # Find optimal assignment
            rows = distances.min(axis=1).argsort()
            cols = distances.argmin(axis=1)[rows]

            used_row_indices = set()
            used_col_indices = set()

            # Update existing objects
            for (row, col) in zip(rows, cols):
                if row in used_row_indices or col in used_col_indices:
                    continue

                if distances[row, col] <= self.max_distance:
                    object_id = object_ids[row]
                    new_centroid = input_centroids[col]
                    new_size = input_sizes[col]
                    
                    # Update object data
                    self.objects[object_id] = new_centroid
                    self.disappeared[object_id] = 0
                    
                    # Update velocity
                    self.object_velocities[object_id] = self.calculate_velocity(
                        object_id, new_centroid
                    )
                    
                    # Update history (keep last 10 positions)
                    if object_id not in self.object_history:
                        self.object_history[object_id] = []
                    self.object_history[object_id].append(new_centroid)
                    if len(self.object_history[object_id]) > 10:
                        self.object_history[object_id].pop(0)
                    
                    # Update size
                    self.object_sizes[object_id] = new_size

                    used_row_indices.add(row)
                    used_col_indices.add(col)

            # Handle unmatched objects and detections
            unused_row_indices = set(range(0, distances.shape[0])).difference(used_row_indices)
            unused_col_indices = set(range(0, distances.shape[1])).difference(used_col_indices)

            if distances.shape[0] >= distances.shape[1]:
                # More objects than detections
                for row in unused_row_indices:
                    object_id = object_ids[row]
                    self.disappeared[object_id] += 1

                    if self.disappeared[object_id] > self.max_disappeared:
                        self.deregister(object_id)
            else:
                # More detections than objects
                for col in unused_col_indices:
                    self.register(input_centroids[col], input_sizes[col])

        return self.objects
    
class LineCounter:
    """
    Simple line crossing counter
    """
    def __init__(self, line_start, line_end):
        self.line_start = line_start
        self.line_end = line_end
        self.in_count = 0
        self.out_count = 0
        self.last_positions = {}

    def _is_above_line(self, point):
        # Determine if a point is above or below the counting line
        (x1, y1), (x2, y2) = self.line_start, self.line_end
        return (point[0] - x1) * (y2 - y1) - (point[1] - y1) * (x2 - x1) > 0

    def count_crossing(self, objects):
        # objects = {id: (x, y)}
        for obj_id, centroid in objects.items():
            current_pos = centroid
            is_above = self._is_above_line(current_pos)

            if obj_id in self.last_positions:
                was_above = self.last_positions[obj_id]
                if was_above != is_above:
                    if is_above:
                        self.in_count += 1
                    else:
                        self.out_count += 1

            self.last_positions[obj_id] = is_above


class EnhancedPeopleCountingSystem:
    """
    Enhanced system with improved tracking
    """
    def __init__(self, model_path=None, conf_threshold=0.3):  # Lower threshold
        # Load YOLOv8 model
        if model_path:
            self.model = YOLO(model_path)
        else:
            self.model = YOLO('yolov8n.pt')
        
        self.conf_threshold = conf_threshold
        self.tracker = ImprovedTracker(max_disappeared=60, max_distance=150)
        
        # Initialize line counter
        self.line_counter = None
        
        # Statistics
        self.total_people_count = 0
        self.current_people_count = 0
        
    def detect_people(self, frame):
        """Enhanced people detection with size information"""
        results = self.model(frame, verbose=False)
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    if cls == 0 and conf > self.conf_threshold:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        # Calculate centroid and size
                        centroid_x = int((x1 + x2) / 2)
                        centroid_y = int((y1 + y2) / 2)
                        width = int(x2 - x1)
                        height = int(y2 - y1)
                        
                        detections.append({
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'centroid': (centroid_x, centroid_y),
                            'size': (width, height),
                            'confidence': conf
                        })
        
        return detections
    
    def process_frame(self, frame):
        """Process frame with enhanced tracking"""
        detections = self.detect_people(frame)
        
        # Prepare data for enhanced tracker
        detections_with_sizes = [
            (det['centroid'], det['size']) for det in detections
        ]
        
        # Update tracker
        tracked_objects = self.tracker.update(detections_with_sizes)
        
        # Initialize line counter if needed
        if self.line_counter is None:
            height, width = frame.shape[:2]
            line_start = (width // 4, height // 2)
            line_end = (3 * width // 4, height // 2)
            from people_count_track import LineCounter  # Import from original
            self.line_counter = LineCounter(line_start, line_end)
        
        # Count line crossings
        self.line_counter.count_crossing(tracked_objects)
        
        # Update counts
        self.current_people_count = len(tracked_objects)
        self.total_people_count = max(self.total_people_count, self.current_people_count)
        
        # Draw visualizations
        vis_frame = self.draw_enhanced_visualizations(frame, detections, tracked_objects)
        
        return vis_frame, tracked_objects
    
    def draw_enhanced_visualizations(self, frame, detections, tracked_objects):
        """Enhanced visualization with tracking history"""
        vis_frame = frame.copy()
        
        # Draw counting line
        if self.line_counter:
            cv2.line(vis_frame, self.line_counter.line_start, 
                    self.line_counter.line_end, (0, 255, 255), 3)
        
        # Map detections to tracked objects
        detection_map = {}
        for det in detections:
            for obj_id, centroid in tracked_objects.items():
                if abs(det['centroid'][0] - centroid[0]) < 30 and \
                   abs(det['centroid'][1] - centroid[1]) < 30:
                    detection_map[obj_id] = det
                    break
        
        # Draw tracking information
        for obj_id, centroid in tracked_objects.items():
            # Draw trajectory (history)
            if obj_id in self.tracker.object_history:
                history = self.tracker.object_history[obj_id]
                if len(history) > 1:
                    for i in range(1, len(history)):
                        cv2.line(vis_frame, history[i-1], history[i], (255, 0, 255), 2)
            
            # Draw predicted position
            predicted_pos = self.tracker.predict_position(obj_id)
            cv2.circle(vis_frame, predicted_pos, 8, (0, 255, 255), 2)
            
            if obj_id in detection_map:
                det = detection_map[obj_id]
                x1, y1, x2, y2 = det['bbox']
                
                # Draw bounding box with different colors based on tracking confidence
                track_age = len(self.tracker.object_history.get(obj_id, []))
                if track_age > 5:
                    color = (0, 255, 0)  # Green for stable tracks
                else:
                    color = (0, 165, 255)  # Orange for new tracks
                
                cv2.rectangle(vis_frame, (x1, y1), (x2, y2), color, 2)
                
                # Enhanced ID label
                label = f"ID:{obj_id}"
                cv2.putText(vis_frame, label, (x1, y1 - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Draw centroid
            cv2.circle(vis_frame, centroid, 5, (255, 0, 0), -1)
        
        # Draw enhanced statistics
        self.draw_enhanced_stats(vis_frame)
        
        return vis_frame
    
    def draw_enhanced_stats(self, frame):
        """Draw enhanced statistics overlay"""
        height, width = frame.shape[:2]
        
        # Create overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (450, 180), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Statistics
        stable_tracks = sum(1 for obj_id in self.tracker.objects.keys() 
                           if len(self.tracker.object_history.get(obj_id, [])) > 5)
        
        stats = [
            f"Current People: {self.current_people_count}",
            f"Stable Tracks: {stable_tracks}",
            f"Peak Count: {self.total_people_count}",
            f"People In: {self.line_counter.in_count if self.line_counter else 0}",
            f"People Out: {self.line_counter.out_count if self.line_counter else 0}",
            f"Total Tracks Created: {self.tracker.next_object_id}"
        ]
        
        for i, stat in enumerate(stats):
            cv2.putText(frame, stat, (20, 35 + i * 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    def run_webcam(self):
        """Run people counting using webcam"""
        cap = cv2.VideoCapture(0)  # Open default webcam
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            vis_frame, tracked_objects = self.process_frame(frame)
            cv2.imshow("Enhanced People Counter", vis_frame)

            # Press 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()


# Usage example
def main_enhanced():
    print("Enhanced People Counting System with Better ID Consistency")
    print("=" * 60)
    
    system = EnhancedPeopleCountingSystem(conf_threshold=0.3)
    system.run_webcam()

if __name__ == "__main__":
    main_enhanced()
