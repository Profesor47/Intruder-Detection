"""
Video Capture Module
Handles real-time video stream acquisition from USB camera or Raspberry Pi camera
"""

import cv2
import threading
import logging
import queue
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class VideoCapture:
    """
    Thread-safe video capture manager.
    Continuously captures frames from camera in background thread.
    """
    
    def __init__(
        self,
        camera_index: int = 0,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
        buffer_size: int = 2
    ):
        """
        Initialize video capture.
        
        Args:
            camera_index: Camera device index (0 for default)
            width: Frame width in pixels
            height: Frame height in pixels
            fps: Target frames per second
            buffer_size: Frame buffer queue size
        """
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.buffer_size = buffer_size
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.frame_queue: queue.Queue = queue.Queue(maxsize=buffer_size)
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize camera connection and settings."""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            
            # Verify camera opened successfully
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera {self.camera_index}")
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer for fresh frames
            
            # Try to set focus properties if available
            try:
                if hasattr(cv2, 'CAP_PROP_AUTOFOCUS'):
                    self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
                if hasattr(cv2, 'CAP_PROP_FOCUS_AUTO'):
                    self.cap.set(cv2.CAP_PROP_FOCUS_AUTO, 1)
            except Exception as focus_error:
                logger.warning(f"Could not set focus properties: {str(focus_error)}")
            
            logger.info(f"✓ Camera initialized (index: {self.camera_index})")
            
            # Start capture thread
            self.running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            
        except Exception as e:
            logger.error(f"Camera initialization error: {str(e)}")
            raise
    
    def _capture_loop(self):
        """
        Continuous frame capture loop running in background thread.
        Captures frames and puts them in queue for consumer.
        """
        while self.running:
            try:
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.warning("Failed to read frame from camera")
                    continue
                
                # Try to put frame in queue (drop if queue full)
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    # Queue full - drop oldest frame
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame)
                    except queue.Empty:
                        self.frame_queue.put_nowait(frame)
                
            except Exception as e:
                logger.error(f"Frame capture error: {str(e)}")
                continue
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get latest captured frame.
        Returns None if no frame available.
        """
        try:
            frame = self.frame_queue.get_nowait()
            return frame
        except queue.Empty:
            return None
    
    def get_frame_blocking(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        Get frame with blocking wait.
        
        Args:
            timeout: Maximum time to wait in seconds
        
        Returns:
            Frame array or None if timeout
        """
        try:
            frame = self.frame_queue.get(timeout=timeout)
            return frame
        except queue.Empty:
            return None
    
    def stop(self):
        """Stop video capture and cleanup."""
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=2.0)
        
        if self.cap:
            self.cap.release()
        
        logger.info("Video capture stopped")
    
    def get_properties(self) -> dict:
        """Get current camera properties."""
        if not self.cap:
            return {}
        
        return {
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": self.cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        }
    
    def __del__(self):
        """Cleanup on object destruction."""
        self.stop()


class VideoRecorder:
    """Records video clips for alert storage."""
    
    def __init__(self, width=1280, height=720, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = None
        self.recording = False
        self.frame_count = 0
        self.output_path = None
    
    def start_recording(self):
        """Start recording video clip."""
        from datetime import datetime
        from pathlib import Path
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_path = Path("./storage/clips") / f"clip_{timestamp}.mp4"
        
        self.writer = cv2.VideoWriter(
            str(self.output_path),
            self.fourcc,
            self.fps,
            (self.width, self.height)
        )
        
        if not self.writer.isOpened():
            logger.error(f"Failed to create video writer: {self.output_path}")
            return False
        
        self.recording = True
        self.frame_count = 0
        logger.info(f"Started recording: {self.output_path}")
        return True
    
    def write_frame(self, frame):
        """Write frame to video file."""
        if self.recording and self.writer:
            self.writer.write(frame)
            self.frame_count += 1
    
    def stop_recording(self):
        """Stop recording and finalize video file."""
        if self.writer:
            self.writer.release()
            self.recording = False
            logger.info(f"Stopped recording: {self.frame_count} frames saved")
            return self.output_path
        return None
    
    def get_duration(self):
        """Get current recording duration in seconds."""
        if self.fps > 0:
            return self.frame_count / self.fps
        return 0.0
