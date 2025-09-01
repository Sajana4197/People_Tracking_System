import cv2
import sys
from detector import PersonDetector
from tracker import MultiObjectTracker
from counter import PeopleCounter
from visualizer import Visualizer

def main():
    # Initialize video capture
    cap = cv2.VideoCapture(0)  # webcam
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    # Set camera resolution (optional)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    try:
        # Initialize components
        detector = PersonDetector(confidence=0.4)  # Lower confidence for better detection
        tracker = MultiObjectTracker(max_age=30, n_init=3)
        
        # Configure for horizontal line counting
        line_position = 240  # Horizontal line position (adjust based on your camera view)
        counter = PeopleCounter(line_position=line_position, direction="horizontal", max_capacity=10)
        visualizer = Visualizer(line_position=line_position, direction="horizontal")
        
        frame_count = 0
        print("People counting system started. Press 'q' to quit, 'r' to reset counts.")
        print("Make sure people cross the RED horizontal line to be counted!")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame")
                break

            frame_count += 1
            
            # Detect people in the frame
            detections = detector.detect(frame)
            
            # Update tracker
            tracked_objects = tracker.update(frame, detections)
            
            # Get active track IDs for cleanup
            active_track_ids = [obj["id"] for obj in tracked_objects]
            
            # Check for line crossings
            for obj in tracked_objects:
                counter.check_crossing(obj["id"], obj["bbox"])
            
            # Cleanup lost tracks from counter memory
            counter.cleanup_lost_tracks(active_track_ids)
            
            # Get current counts
            count_in, count_out = counter.get_counts()
            over_capacity, current_inside = counter.is_over_capacity()
            
            # Draw visualization
            frame = visualizer.draw(frame, tracked_objects, count_in, count_out, over_capacity, current_inside)
            
            # Add frame counter
            cv2.putText(frame, f"Frame: {frame_count}", (10, frame.shape[0] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show frame
            cv2.imshow("People Counter & Tracker", frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("Quitting...")
                break
            elif key == ord("r"):
                print("Resetting counts...")
                counter.reset_counts()
                print(f"Counts reset. In: {counter.count_in}, Out: {counter.count_out}")

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        
        # Final statistics
        count_in, count_out = counter.get_counts()
        current_inside = counter.get_current_inside()
        print("\nFinal Statistics:")
        print(f"People entered: {count_in}")
        print(f"People exited: {count_out}")
        print(f"Currently inside: {current_inside}")

if __name__ == "__main__":
    main()