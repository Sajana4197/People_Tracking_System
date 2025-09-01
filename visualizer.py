import cv2

class Visualizer:
    def __init__(self, line_position=300, direction="horizontal"):
        self.line_position = line_position
        self.direction = direction

    def draw(self, frame, tracked_objects, count_in, count_out, over_capacity=False, current_inside=0):
        h, w = frame.shape[:2]
        
        # Draw tracked objects with tight bounding boxes
        for obj in tracked_objects:
            x1, y1, x2, y2 = obj["bbox"]
            
            # Ensure coordinates are within frame bounds
            x1 = max(0, min(x1, w-1))
            y1 = max(0, min(y1, h-1))
            x2 = max(0, min(x2, w-1))
            y2 = max(0, min(y2, h-1))
            
            # Draw tight bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw ID with background for better visibility
            label = f"ID {obj['id']}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # Background rectangle for text
            cv2.rectangle(frame, (x1, y1-25), (x1 + label_size[0] + 5, y1), (0, 255, 0), -1)
            cv2.putText(frame, label, (x1 + 2, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        # Draw counting line
        if self.direction == "horizontal":
            # Horizontal line (people cross vertically)
            line_y = max(0, min(self.line_position, h-1))
            cv2.line(frame, (0, line_y), (w, line_y), (0, 0, 255), 3)
            
            # Add arrows to show direction
            cv2.arrowedLine(frame, (50, line_y - 20), (50, line_y - 5), (0, 255, 255), 2)
            cv2.putText(frame, "IN", (55, line_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            cv2.arrowedLine(frame, (100, line_y + 20), (100, line_y + 5), (255, 0, 255), 2)
            cv2.putText(frame, "OUT", (105, line_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
            
        else:  # vertical line
            # Vertical line (people cross horizontally)
            line_x = max(0, min(self.line_position, w-1))
            cv2.line(frame, (line_x, 0), (line_x, h), (0, 0, 255), 3)
            
            # Add arrows to show direction
            cv2.arrowedLine(frame, (line_x - 20, 50), (line_x - 5, 50), (0, 255, 255), 2)
            cv2.putText(frame, "IN", (line_x - 45, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            cv2.arrowedLine(frame, (line_x + 20, 100), (line_x + 5, 100), (255, 0, 255), 2)
            cv2.putText(frame, "OUT", (line_x + 25, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)

        # Draw statistics with background
        stats_bg_color = (0, 0, 0)  # Black background
        text_color = (255, 255, 255)  # White text
        
        # Background rectangles for better readability
        cv2.rectangle(frame, (10, 10), (350, 100), stats_bg_color, -1)
        
        # Draw counts
        cv2.putText(frame, f"In: {count_in}  Out: {count_out}", (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, text_color, 2)
        cv2.putText(frame, f"Currently Inside: {current_inside}", (20, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, text_color, 2)
        cv2.putText(frame, f"Active Tracks: {len(tracked_objects)}", (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Warning if over capacity
        if over_capacity:
            warning_text = "!!! WARNING: OVER CAPACITY !!!"
            text_size = cv2.getTextSize(warning_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 4)[0]
            
            # Center the warning
            text_x = (w - text_size[0]) // 2
            text_y = h - 50
            
            # Background for warning
            cv2.rectangle(frame, (text_x - 10, text_y - 30), (text_x + text_size[0] + 10, text_y + 10), (0, 0, 255), -1)
            cv2.putText(frame, warning_text, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 4)

        return frame