"""
Intruder Tracking Module
Real-time multi-object tracking with ByteTrack
Handles automatic motor control to follow intruders
"""

import logging
import numpy as np
from typing import List, Dict, Optional
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


class Track:
    """Represents a tracked object (person)."""
    
    def __init__(self, track_id: str, detection: Dict):
        self.track_id = track_id
        self.bbox = detection["bbox"]
        self.confidence = detection.get("confidence", 0)
        self.face_id = detection.get("face_id")
        self.face_confidence = detection.get("face_confidence", 0)
        
        self.frame_count = 0
        self.hit_count = 0
        self.age = 0
        self.is_confirmed = False
        
        # Trajectory history
        self.trajectory = [self._get_center()]
        self.last_detection_frame = 0
    
    def update(self, detection: Dict):
        """Update track with new detection."""
        self.bbox = detection["bbox"]
        self.confidence = detection.get("confidence", 0)
        self.face_id = detection.get("face_id")
        self.face_confidence = detection.get("face_confidence", 0)
        
        self.hit_count += 1
        self.frame_count += 1
        self.last_detection_frame = self.frame_count
        
        # Confirm track after MIN_HITS
        if self.hit_count >= 3:
            self.is_confirmed = True
        
        self.trajectory.append(self._get_center())
        
        # Keep only last 30 points
        if len(self.trajectory) > 30:
            self.trajectory = self.trajectory[-30:]
    
    def age_track(self):
        """Increment age (called when no detection)."""
        self.age += 1
    
    def _get_center(self) -> tuple:
        """Get center of bounding box."""
        x, y, w, h = self.bbox
        return (x + w // 2, y + h // 2)
    
    def get_center(self) -> tuple:
        """Get current center."""
        return self._get_center()
    
    def get_deviation_from_center(self, frame_width: int) -> float:
        """
        Get deviation from frame center (-1 to 1).
        Negative = left, Positive = right
        """
        center_x = self.get_center()[0]
        frame_center = frame_width / 2
        deviation = (center_x - frame_center) / (frame_width / 2)
        return np.clip(deviation, -1.0, 1.0)


class IntruderTracker:
    """
    Multi-object tracker using simple centroid tracking.
    Falls back when ByteTrack not available.
    """
    
    def __init__(
        self,
        max_distance: float = 100,
        max_age: int = 30,
        min_hits: int = 3
    ):
        """
        Initialize tracker.
        
        Args:
            max_distance: Maximum distance for track association
            max_age: Max frames to keep track without detection
            min_hits: Frames before track is confirmed
        """
        self.max_distance = max_distance
        self.max_age = max_age
        self.min_hits = min_hits
        
        self.tracks: Dict[str, Track] = {}
        self.track_counter = 0
        self.frame_count = 0
        
        self.auto_track_enabled = True
        self.tracked_intruder_id: Optional[str] = None
        
        self._try_load_bytetrack()
    
    def _try_load_bytetrack(self):
        """Try to load ByteTrack for more advanced tracking."""
        try:
            from bytetrack import ByteTrack
            self.byte_tracker = ByteTrack()
            logger.info("✓ ByteTrack loaded")
        except ImportError:
            logger.info("ByteTrack not available, using centroid tracking")
            self.byte_tracker = None
    
    def update(self, detections: List[Dict]) -> List[Dict]:
        """
        Update tracks with new detections.
        
        Args:
            detections: List of new detections
        
        Returns:
            List of tracked objects with track IDs
        """
        self.frame_count += 1
        tracked_objects = []
        
        if not detections:
            # Age all tracks
            for track in self.tracks.values():
                track.age_track()
            
            # Remove dead tracks
            self._prune_tracks()
            return []
        
        if self.byte_tracker:
            return self._update_bytetrack(detections)
        else:
            return self._update_centroid(detections)
    
    def _update_centroid(self, detections: List[Dict]) -> List[Dict]:
        """Simple centroid-based tracking."""
        tracked_objects = []
        used_track_ids = set()
        
        # Match detections to existing tracks
        for detection in detections:
            best_track_id = None
            best_distance = float('inf')
            
            det_center = (
                detection["x1"] + (detection["x2"] - detection["x1"]) // 2,
                detection["y1"] + (detection["y2"] - detection["y1"]) // 2
            )
            
            for track_id, track in self.tracks.items():
                if track_id in used_track_ids or track.age > 0:
                    continue
                
                track_center = track.get_center()
                distance = np.sqrt(
                    (det_center[0] - track_center[0])**2 +
                    (det_center[1] - track_center[1])**2
                )
                
                if distance < best_distance and distance < self.max_distance:
                    best_distance = distance
                    best_track_id = track_id
            
            # Update or create track
            if best_track_id:
                self.tracks[best_track_id].update(detection)
                used_track_ids.add(best_track_id)
                detection["track_id"] = best_track_id
            else:
                # Create new track
                new_track_id = str(uuid.uuid4())
                self.tracks[new_track_id] = Track(new_track_id, detection)
                detection["track_id"] = new_track_id
            
            tracked_objects.append(detection)
        
        # Age unmatched tracks
        for track_id, track in self.tracks.items():
            if track_id not in used_track_ids:
                track.age_track()
        
        # Remove dead tracks
        self._prune_tracks()
        
        return tracked_objects
    
    def _update_bytetrack(self, detections: List[Dict]) -> List[Dict]:
        """Advanced tracking with ByteTrack."""
        if not self.byte_tracker:
            return self._update_centroid(detections)
        
        try:
            # Convert detections to ByteTrack format
            online_targets = self.byte_tracker.update(detections)
            
            tracked_objects = []
            for target in online_targets:
                detection = {
                    "track_id": str(target.track_id),
                    "bbox": target.bbox,
                    "confidence": target.conf
                }
                tracked_objects.append(detection)
            
            return tracked_objects
        
        except Exception as e:
            logger.error(f"ByteTrack error: {str(e)}, falling back")
            return self._update_centroid(detections)
    
    def _prune_tracks(self):
        """Remove old/dead tracks."""
        dead_ids = [
            tid for tid, track in self.tracks.items()
            if track.age > self.max_age
        ]
        for tid in dead_ids:
            del self.tracks[tid]
    
    def set_auto_track(self, enabled: bool):
        """Enable/disable automatic tracking of first intruder."""
        self.auto_track_enabled = enabled
        if not enabled:
            self.tracked_intruder_id = None
    
    def get_auto_track_target(self) -> Optional[Dict]:
        """Get target for automatic motor tracking."""
        if not self.auto_track_enabled:
            return None
        
        # Get first unknown/intruder track
        for track_id, track in self.tracks.items():
            if track.is_confirmed and track.face_id is None:
                self.tracked_intruder_id = track_id
                return {
                    "track_id": track_id,
                    "center": track.get_center(),
                    "bbox": track.bbox,
                    "confidence": track.confidence
                }
        
        return None
    
    def get_motor_control(
        self,
        target: Optional[Dict],
        frame_width: int,
        frame_height: int
    ) -> Optional[Dict]:
        """
        Calculate motor control based on target position.
        
        Args:
            target: Target object from get_auto_track_target
            frame_width: Video frame width
            frame_height: Video frame height
        
        Returns:
            Motor control dict or None
        """
        if not target:
            return None
        
        center_x, center_y = target["center"]
        
        # Calculate deviations
        horizontal_deviation = (center_x - frame_width/2) / (frame_width/2)
        vertical_deviation = (center_y - frame_height/2) / (frame_height/2)
        
        horizontal_deviation = np.clip(horizontal_deviation, -1.0, 1.0)
        vertical_deviation = np.clip(vertical_deviation, -1.0, 1.0)
        
        # Calculate motor speeds
        left_motor_speed = 128 + int(horizontal_deviation * 127)
        right_motor_speed = 128 - int(horizontal_deviation * 127)
        
        up_motor_speed = 128 + int(vertical_deviation * 127)
        down_motor_speed = 128 - int(vertical_deviation * 127)
        
        return {
            "track_id": target["track_id"],
            "horizontal_deviation": horizontal_deviation,
            "vertical_deviation": vertical_deviation,
            "left_motor_speed": left_motor_speed,
            "right_motor_speed": right_motor_speed,
            "up_motor_speed": up_motor_speed,
            "down_motor_speed": down_motor_speed
        }
    
    def get_tracks(self, confirmed_only: bool = True) -> List[Dict]:
        """Get current tracks."""
        tracks = []
        for track_id, track in self.tracks.items():
            if confirmed_only and not track.is_confirmed:
                continue
            
            tracks.append({
                "track_id": track_id,
                "bbox": track.bbox,
                "center": track.get_center(),
                "confidence": track.confidence,
                "face_id": track.face_id,
                "face_confidence": track.face_confidence,
                "age": track.age,
                "is_confirmed": track.is_confirmed,
                "trajectory": track.trajectory
            })
        
        return tracks
