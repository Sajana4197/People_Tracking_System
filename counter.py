import cv2

class PeopleCounter:
    def __init__(self, line_position=300, direction="horizontal", max_capacity=50):
        self.line_position = line_position
        self.direction = direction
        self.count_in = 0
        self.count_out = 0
        self.track_memory = {}
        self.max_capacity = max_capacity
        self.track_states = {}  # Track which side of line each person is on

    def check_crossing(self, track_id, bbox):
        x1, y1, x2, y2 = bbox
        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

        # Use correct coordinate based on direction
        current_pos = cy if self.direction == "horizontal" else cx

        if track_id not in self.track_memory:
            # First time seeing this track - just store position
            self.track_memory[track_id] = current_pos
            # Determine initial side of the line
            if self.direction == "horizontal":
                self.track_states[track_id] = "above" if cy < self.line_position else "below"
            else:
                self.track_states[track_id] = "left" if cx < self.line_position else "right"
            return

        prev_pos = self.track_memory[track_id]
        prev_state = self.track_states.get(track_id)

        if self.direction == "horizontal":
            # Horizontal line crossing (people move up/down)
            current_state = "above" if cy < self.line_position else "below"
            
            # Check for crossing
            if prev_state == "above" and current_state == "below":
                self.count_in += 1  # Crossing from above to below = entering
                print(f"Person {track_id} entered (above->below)")
            elif prev_state == "below" and current_state == "above":
                self.count_out += 1  # Crossing from below to above = exiting
                print(f"Person {track_id} exited (below->above)")
                
        else:  # Vertical line crossing
            # Vertical line crossing (people move left/right)
            current_state = "left" if cx < self.line_position else "right"
            
            # Check for crossing
            if prev_state == "left" and current_state == "right":
                self.count_in += 1  # Crossing from left to right = entering
                print(f"Person {track_id} entered (left->right)")
            elif prev_state == "right" and current_state == "left":
                self.count_out += 1  # Crossing from right to left = exiting
                print(f"Person {track_id} exited (right->left)")

        # Update memory
        self.track_memory[track_id] = current_pos
        self.track_states[track_id] = current_state

    def cleanup_lost_tracks(self, active_track_ids):
        """Remove tracking data for tracks that are no longer active"""
        lost_tracks = set(self.track_memory.keys()) - set(active_track_ids)
        for track_id in lost_tracks:
            if track_id in self.track_memory:
                del self.track_memory[track_id]
            if track_id in self.track_states:
                del self.track_states[track_id]

    def get_counts(self):
        return self.count_in, self.count_out

    def get_current_inside(self):
        return max(0, self.count_in - self.count_out)

    def is_over_capacity(self):
        current_inside = self.get_current_inside()
        return current_inside > self.max_capacity, current_inside

    def reset_counts(self):
        """Reset all counts and tracking data"""
        self.count_in = 0
        self.count_out = 0
        self.track_memory.clear()
        self.track_states.clear()