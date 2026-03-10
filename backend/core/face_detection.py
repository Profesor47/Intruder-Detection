"""
Face Detection Module
Uses YOLOv8-face model for real-time face detection on Raspberry Pi
"""

import cv2
import logging
import numpy as np
from typing import List, Dict, Tuple
import os

logger = logging.getLogger(__name__)


class FaceDetector:
    """
    Real-time face detection using YOLOv8.
    Optimized for Raspberry Pi with low latency.
    """
    
    def __init__(self, model_path: str = "models/yolov8n-face.pt", confidence: float = 0.5):
        """
        Initialize face detector.
        
        Args:
            model_path: Path to YOLOv8 model weights
            confidence: Detection confidence threshold (0-1)
        """
        self.model_path = model_path
        self.confidence = confidence
        self.model = None
        
        self._load_model()
    
    def _load_model(self):
        """Load YOLOv8 model."""
        try:
            # Try to import ultralytics - if not available, use fallback
            try:
                from ultralytics import YOLO
                
                if not os.path.exists(self.model_path):
                    logger.warning(f"Model not found at {self.model_path}")
                    logger.info("Downloading YOLOv8-face model...")
                    # Model will be auto-downloaded
                
                self.model = YOLO(self.model_path)
                logger.info(f"✓ YOLOv8 model loaded: {self.model_path}")
                
            except ImportError:
                logger.warning("ultralytics not installed, using fallback HOG detector")
                self.model = None  # Will use HOG cascade fallback
        
        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model: {str(e)}")
            logger.info("Falling back to cascade classifier")
            self.model = None
    
    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect faces in frame.
        
        Args:
            frame: Input image frame (BGR format)
        
        Returns:
            List of detections with bounding boxes and confidence scores
        """
        if frame is None or frame.size == 0:
            return []
        
        detections = []
        
        try:
            if self.model:
                # Use YOLOv8
                detections = self._detect_yolo(frame)
            else:
                # Fallback to cascade classifier
                detections = self._detect_cascade(frame)
        
        except Exception as e:
            logger.error(f"Detection error: {str(e)}")
            detections = []
        
        return detections
    
    def _detect_yolo(self, frame: np.ndarray) -> List[Dict]:
        """Detect using YOLOv8 model."""
        try:
            results = self.model.predict(
                frame,
                conf=self.confidence,
                verbose=False,
                device=0  # Auto-select device (CPU on Pi)
            )
            
            detections = []
            
            if results and len(results) > 0:
                result = results[0]
                
                for box in result.boxes:
                    if box.conf[0] >= self.confidence:
                        # Extract coordinates
                        x1, y1, x2, y2 = box.xyxy[0]
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        width = x2 - x1
                        height = y2 - y1
                        confidence = float(box.conf[0])
                        
                        detections.append({
                            "bbox": [x1, y1, width, height],
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                            "confidence": confidence,
                            "class": "face"
                        })
            
            return detections
        
        except Exception as e:
            logger.error(f"YOLOv8 detection error: {str(e)}")
            return []
    
    def _detect_cascade(self, frame: np.ndarray) -> List[Dict]:
        """Fallback cascade classifier detection."""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Load cascade classifier
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            cascade = cv2.CascadeClassifier(cascade_path)
            
            faces = cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            detections = []
            for (x, y, w, h) in faces:
                detections.append({
                    "bbox": [x, y, w, h],
                    "x1": x,
                    "y1": y,
                    "x2": x + w,
                    "y2": y + h,
                    "confidence": 0.9,  # Cascade doesn't provide confidence
                    "class": "face"
                })
            
            return detections
        
        except Exception as e:
            logger.error(f"Cascade detection error: {str(e)}")
            return []
    
    def get_face_roi(self, frame: np.ndarray, detection: Dict) -> np.ndarray:
        """Extract face region of interest from frame."""
        x1 = detection["x1"]
        y1 = detection["y1"]
        x2 = detection["x2"]
        y2 = detection["y2"]
        
        return frame[y1:y2, x1:x2]
    
    def visualize_detections(
        self,
        frame: np.ndarray,
        detections: List[Dict],
        thickness: int = 2
    ) -> np.ndarray:
        """Draw detection boxes on frame."""
        annotated = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det["x1"], det["y1"], det["x2"], det["y2"]
            confidence = det.get("confidence", 0)
            
            # Draw bounding box
            color = (0, 255, 0)  # Green
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
            
            # Draw confidence score
            label = f"Face {confidence:.2f}"
            cv2.putText(
                annotated,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                thickness
            )
        
        return annotated
