import cv2
import os
import sys
import torch
import numpy as np

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class PersonDetector:
    def __init__(self, model_path="yolov8n.pt", confidence=0.5):
        self.confidence = confidence
        self.model = None
        self.preprocessing_enabled = True
        
        try:
            # Use resource_path for model file
            actual_model_path = resource_path(model_path)
            
            try:
                from ultralytics.nn.tasks import DetectionModel
                torch.serialization.add_safe_globals([DetectionModel])
            except:
                pass
            
            from ultralytics import YOLO
            self.model = YOLO(actual_model_path)
            print(f"Model loaded successfully: {actual_model_path}")
            
            # Warm up the model
            dummy_input = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            self.model(dummy_input, verbose=False)
            
        except ImportError:
            print("Warning: ultralytics module not available. Install with: pip install ultralytics")
        except Exception as e:
            print(f"Error loading model: {e}")
            # Try fallback loading method
            try:
                # Load with weights_only=False for compatibility
                from ultralytics import YOLO
                self.model = YOLO(actual_model_path, weights_only=False)
                print(f"Model loaded with fallback method: {actual_model_path}")
            except Exception as e2:
                print(f"Fallback loading also failed: {e2}")

    def preprocess_frame(self, frame):
        """Apply preprocessing to improve detection"""
        if not self.preprocessing_enabled:
            return frame
            
        # Convert to HSV color space for better contrast
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Apply histogram equalization to the value channel
        h, s, v = cv2.split(hsv)
        v = cv2.equalizeHist(v)
        hsv = cv2.merge([h, s, v])
        
        # Convert back to BGR
        enhanced = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        # Apply mild sharpening
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        return sharpened

    def detect(self, frame):
        if self.model is None:
            return []
            
        try:
            # Preprocess the frame for better detection
            processed_frame = self.preprocess_frame(frame)
            
            # Run detection
            results = self.model(processed_frame, verbose=False)[0]
            detections = []
            
            if results.boxes is not None:
                for box in results.boxes:
                    # Check if detection is a person (class 0 in COCO dataset)
                    if int(box.cls[0]) == 0 and float(box.conf[0]) >= self.confidence:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        conf = float(box.conf[0])
                        
                        # Ensure valid bounding box
                        if x2 > x1 and y2 > y1:
                            # Expand bounding box slightly for better tracking
                            padding = 5
                            x1 = max(0, x1 - padding)
                            y1 = max(0, y1 - padding)
                            x2 = min(frame.shape[1], x2 + padding)
                            y2 = min(frame.shape[0], y2 + padding)
                            
                            detections.append(([x1, y1, x2, y2], conf, "person"))
            
            return detections
            
        except Exception as e:
            print(f"Error in detection: {e}")
            return []
            
    def enable_preprocessing(self, enable):
        """Enable or disable frame preprocessing"""
        self.preprocessing_enabled = enable
        
    def set_confidence(self, confidence):
        """Update detection confidence threshold"""
        self.confidence = confidence
