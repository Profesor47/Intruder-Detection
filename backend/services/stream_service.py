"""
Stream Service
Video frame annotation and MJPEG encoding for real-time streaming
"""

import cv2
import logging
import numpy as np
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class StreamService:
    """Video streaming and annotation service."""
    
    def __init__(self):
        """Initialize stream service."""
        self.frame_count = 0
        self.last_fps_time = datetime.now()
        self.fps = 0
    
    def annotate_frame(
        self,
        frame: np.ndarray,
        tracked_objects: List[Dict],
        draw_trajectory: bool = True
    ) -> np.ndarray:
        """
        Annotate frame with detections and tracking information.
        
        Args:
            frame: Original frame
            tracked_objects: List of tracked object dicts
            draw_trajectory: Whether to draw tracking trajectory
        
        Returns:
            Annotated frame
        """
        annotated = frame.copy()
        
        for obj in tracked_objects:
            self._draw_detection_box(annotated, obj)
            
            if draw_trajectory and "trajectory" in obj:
                self._draw_trajectory(annotated, obj["trajectory"])
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(
            annotated,
            timestamp,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )
        
        # Add FPS
        cv2.putText(
            annotated,
            f"FPS: {self.fps:.1f}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )
        
        # Add detection count
        cv2.putText(
            annotated,
            f"Objects: {len(tracked_objects)}",
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )
        
        return annotated
    
    def _draw_detection_box(self, frame: np.ndarray, obj: Dict):
        """Draw detection bounding box."""
        if "bbox" in obj:
            x, y, w, h = obj["bbox"]
            x2 = x + w
            y2 = y + h
        elif all(k in obj for k in ["x1", "y1", "x2", "y2"]):
            x, y = obj["x1"], obj["y1"]
            x2, y2 = obj["x2"], obj["y2"]
        else:
            return
        
        # Determine color based on detection type
        if obj.get("face_id"):
            # Known person - green
            color = (0, 255, 0)
            label = f"Known: {obj.get('face_id', 'Unknown')}"
        else:
            # Unknown/intruder - red
            color = (0, 0, 255)
            label = "INTRUDER"
        
        # Draw bounding box
        thickness = 2
        cv2.rectangle(frame, (x, y), (x2, y2), color, thickness)
        
        # Draw label background
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
        cv2.rectangle(
            frame,
            (x, y - label_size[1] - 5),
            (x + label_size[0] + 5, y),
            color,
            -1
        )
        
        # Draw label text
        cv2.putText(
            frame,
            label,
            (x + 2, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1
        )
        
        # Draw confidence if available
        if "confidence" in obj:
            conf_text = f"{obj['confidence']:.1%}"
            cv2.putText(
                frame,
                conf_text,
                (x, y2 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1
            )
        
        # Draw track ID if available
        if "track_id" in obj:
            track_text = f"ID: {obj['track_id'][:8]}"
            cv2.putText(
                frame,
                track_text,
                (x, y2 + 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1
            )
    
    def _draw_trajectory(self, frame: np.ndarray, trajectory: List[tuple]):
        """Draw object trajectory."""
        if len(trajectory) < 2:
            return
        
        for i in range(1, len(trajectory)):
            pt1 = trajectory[i-1]
            pt2 = trajectory[i]
            
            if pt1 and pt2:
                # Color based on age (gradient)
                alpha = i / len(trajectory)
                color = (
                    int(255 * (1 - alpha)),  # Blue channel fades
                    255,  # Green stays
                    int(255 * alpha)  # Red fades in
                )
                
                cv2.line(frame, pt1, pt2, color, 2)
        
        # Draw latest position as circle
        if trajectory:
            latest = trajectory[-1]
            cv2.circle(frame, latest, 5, (0, 255, 0), -1)
    
    def add_detection_zone(
        self,
        frame: np.ndarray,
        zone_coords: tuple,
        label: str = "Detection Zone"
    ) -> np.ndarray:
        """Add detection zone overlay."""
        x1, y1, x2, y2 = zone_coords
        
        # Draw semi-transparent rectangle
        overlay = frame.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (255, 0, 0), 2)
        cv2.addWeighted(overlay, 0.1, frame, 0.9, 0, frame)
        
        # Draw label
        cv2.putText(
            frame,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 0, 0),
            1
        )
        
        return frame
    
    def create_alert_frame(
        self,
        frame: np.ndarray,
        alert_type: str = "INTRUDER"
    ) -> np.ndarray:
        """Create frame with alert overlay."""
        alert_frame = frame.copy()
        
        # Add alert banner
        height = frame.shape[0]
        width = frame.shape[1]
        
        # Red banner at top
        cv2.rectangle(alert_frame, (0, 0), (width, 100), (0, 0, 255), -1)
        
        # Alert text
        cv2.putText(
            alert_frame,
            f"🚨 {alert_type} DETECTED! 🚨",
            (50, 50),
            cv2.FONT_HERSHEY_BOLD,
            1.5,
            (0, 255, 255),
            3
        )
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(
            alert_frame,
            f"Time: {timestamp}",
            (50, height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )
        
        return alert_frame
    
    def resize_frame(
        self,
        frame: np.ndarray,
        width: int = 640,
        height: int = 480
    ) -> np.ndarray:
        """Resize frame while maintaining aspect ratio."""
        return cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)
    
    def encode_frame_jpeg(
        self,
        frame: np.ndarray,
        quality: int = 80
    ) -> bytes:
        """Encode frame as JPEG bytes."""
        _, buffer = cv2.imencode(
            '.jpg',
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, quality]
        )
        return buffer.tobytes()
    
    def update_fps(self, frame_time: float = 1.0):
        """Update FPS counter."""
        self.frame_count += 1
        
        elapsed = (datetime.now() - self.last_fps_time).total_seconds()
        if elapsed >= frame_time:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_time = datetime.now()
    
    def create_collage(
        self,
        frames: List[np.ndarray],
        grid_size: tuple = (2, 2)
    ) -> np.ndarray:
        """
        Create collage of multiple frames.
        
        Args:
            frames: List of frame arrays
            grid_size: (rows, cols) grid layout
        
        Returns:
            Collage image
        """
        rows, cols = grid_size
        
        if len(frames) == 0:
            return np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Resize all frames to same size
        frame_height, frame_width = frames[0].shape[:2]
        resized_frames = [
            cv2.resize(f, (frame_width, frame_height))
            for f in frames
        ]
        
        # Pad with black if needed
        while len(resized_frames) < rows * cols:
            resized_frames.append(
                np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
            )
        
        # Create collage
        row_images = []
        for r in range(rows):
            start_idx = r * cols
            end_idx = start_idx + cols
            row_frames = resized_frames[start_idx:end_idx]
            row_image = cv2.hconcat(row_frames)
            row_images.append(row_image)
        
        collage = cv2.vconcat(row_images)
        return collage
