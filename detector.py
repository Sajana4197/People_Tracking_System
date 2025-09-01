import cv2
from ultralytics import YOLO

class PersonDetector:
    def __init__(self, model_path="yolov8n.pt", confidence=0.5):
        try:
            self.model = YOLO(model_path)
            self.confidence = confidence
            print(f"Model loaded successfully: {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise

    def detect(self, frame):
        try:
            results = self.model(frame, verbose=False)[0]
            detections = []
            
            if results.boxes is not None:
                for box in results.boxes:
                    # Check if detection is a person (class 0 in COCO dataset)
                    if int(box.cls[0]) == 0 and float(box.conf[0]) >= self.confidence:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        conf = float(box.conf[0])
                        
                        # Ensure valid bounding box
                        if x2 > x1 and y2 > y1:
                            detections.append(([x1, y1, x2, y2], conf, "person"))
            
            return detections
            
        except Exception as e:
            print(f"Error in detection: {e}")
            return []